# Requirements Document

## Introduction

판매 완료 폴링 및 타 플랫폼 자동 삭제 기능은 파라파라에 등록된 상품이 하나의 플랫폼(예: 번개장터)에서 판매 완료되면, 나머지 플랫폼(당근/fruits/차란 등)에서 해당 상품을 자동으로 삭제하는 기능입니다. 이는 SSOT(Single Source of Truth) 원칙에 따라 표준_상품(Product) 상태를 중심으로 모든 플랫폼 리스팅을 동기화합니다.

## Glossary

- **Poller**: 각 플랫폼의 active 리스팅을 주기적으로 확인하여 판매 완료 여부를 감지하는 백그라운드 워커
- **Product**: 파라파라의 표준_상품 엔티티. SSOT 원칙에 따라 유일한 원본 데이터
- **Listing**: 특정 플랫폼에 등록된 상품. 하나의 Product는 여러 Listing을 가질 수 있음
- **Sale**: 판매 완료 기록. 어느 플랫폼에서 언제 판매되었는지 기록
- **PlatformAdapter**: 각 플랫폼의 is_sold(), delete_listing() 인터페이스를 구현한 어댑터
- **SoldSyncService**: 판매 완료 감지 시 나머지 플랫폼 리스팅 삭제를 조율하는 서비스

## Requirements

### Requirement 1: 판매 완료 감지 폴링

**User Story:** As a 판매자, I want 각 플랫폼의 판매 완료 상태가 자동으로 감지되기를, so that 수동으로 확인하지 않아도 됩니다.

#### Acceptance Criteria

1. WHEN Poller가 실행되면, THE Poller SHALL 모든 active 상태의 Listing을 조회한다
2. FOR ALL active Listing, THE Poller SHALL 해당 플랫폼의 PlatformAdapter.is_sold()를 호출하여 판매 완료 여부를 확인한다
3. WHEN PlatformAdapter.is_sold()가 True를 반환하면, THE Poller SHALL SoldSyncService.sync_sold()를 호출한다
4. THE Poller SHALL 60초 주기로 폴링을 반복한다
5. WHEN 폴링 중 특정 플랫폼에서 오류가 발생하면, THE Poller SHALL 해당 플랫폼을 건너뛰고 나머지 플랫폼 폴링을 계속한다

### Requirement 2: 표준_상품 상태 업데이트

**User Story:** As a 시스템, I want 판매 완료된 상품의 표준_상품 상태를 sold로 변경하기를, so that SSOT 원칙이 유지됩니다.

#### Acceptance Criteria

1. WHEN SoldSyncService.sync_sold()가 호출되면, THE SoldSyncService SHALL 해당 Product의 status를 sold로 변경한다
2. WHEN Product 상태가 sold로 변경되면, THE SoldSyncService SHALL 판매된 Listing의 status를 sold로 변경한다
3. WHEN Product 상태가 sold로 변경되면, THE SoldSyncService SHALL Sale 레코드를 생성한다
4. THE Sale 레코드 SHALL product_id, listing_id, platform, sold_at 필드를 포함한다

### Requirement 3: 타 플랫폼 리스팅 자동 삭제

**User Story:** As a 판매자, I want 하나의 플랫폼에서 판매 완료되면 나머지 플랫폼에서 자동으로 삭제되기를, so that 중복 판매를 방지할 수 있습니다.

#### Acceptance Criteria

1. WHEN SoldSyncService.sync_sold()가 호출되면, THE SoldSyncService SHALL 판매된 Listing을 제외한 모든 active Listing을 조회한다
2. FOR ALL 조회된 active Listing, THE SoldSyncService SHALL 해당 플랫폼의 PlatformAdapter.delete_listing()을 호출한다
3. WHEN PlatformAdapter.delete_listing()이 성공하면, THE SoldSyncService SHALL 해당 Listing의 status를 removed로 변경한다
4. THE SoldSyncService SHALL 각 플랫폼 삭제 작업을 순차적으로 실행한다

### Requirement 4: 부분 실패 격리

**User Story:** As a 시스템, I want 한 플랫폼의 삭제 실패가 다른 플랫폼 삭제를 막지 않기를, so that 부분 실패 격리 원칙이 준수됩니다.

#### Acceptance Criteria

1. WHEN 특정 플랫폼의 PlatformAdapter.delete_listing()이 실패하면, THE SoldSyncService SHALL 오류를 로깅하고 다음 플랫폼 삭제를 계속한다
2. WHEN PlatformAdapter.delete_listing()이 실패하면, THE SoldSyncService SHALL 해당 Listing의 status를 active로 유지한다
3. FOR ALL 플랫폼 삭제 작업, THE SoldSyncService SHALL try-except 블록으로 각각을 격리한다
4. WHEN 모든 삭제 작업이 완료되면, THE SoldSyncService SHALL 성공 개수와 실패 개수를 반환한다

### Requirement 5: 오류 로깅 및 비밀 정보 보호

**User Story:** As a 개발자, I want 오류 로그에서 문제를 진단할 수 있기를, so that 운영 중 문제를 빠르게 해결할 수 있습니다.

#### Acceptance Criteria

1. WHEN Poller 또는 SoldSyncService에서 오류가 발생하면, THE System SHALL 오류 메시지, 플랫폼명, product_id, listing_id를 로깅한다
2. THE System SHALL 로그에 플랫폼 자격증명(username, password, session token)을 포함하지 않는다
3. THE System SHALL 로그에 Claude API 키 또는 AWS 자격증명을 포함하지 않는다
4. WHEN PlatformAdapter에서 PlatformError가 발생하면, THE System SHALL 오류 메시지에 자격증명을 포함하지 않는다

### Requirement 6: 폴링 워커 배포 지원

**User Story:** As a 운영자, I want Poller를 ECS Fargate 또는 Lambda로 배포할 수 있기를, so that 안정적으로 폴링 작업을 실행할 수 있습니다.

#### Acceptance Criteria

1. THE Poller SHALL asyncio 기반 비동기 실행을 지원한다
2. THE Poller SHALL 환경변수로 폴링 주기를 설정할 수 있다
3. WHEN Poller가 시작되면, THE Poller SHALL 데이터베이스 연결을 초기화한다
4. WHEN Poller가 종료 신호를 받으면, THE Poller SHALL 현재 폴링 사이클을 완료하고 graceful shutdown을 수행한다

### Requirement 7: 동시성 제어

**User Story:** As a 시스템, I want 동일한 Product에 대해 중복 동기화가 발생하지 않기를, so that 데이터 일관성이 유지됩니다.

#### Acceptance Criteria

1. WHEN 동일한 Product의 여러 Listing에서 동시에 판매 완료가 감지되면, THE SoldSyncService SHALL 첫 번째 호출만 처리하고 나머지는 무시한다
2. THE SoldSyncService SHALL Product.status를 확인하여 이미 sold 상태이면 조기 반환한다
3. WHEN Product.status가 sold로 변경되면, THE SoldSyncService SHALL 데이터베이스 트랜잭션으로 원자성을 보장한다

### Requirement 8: PlatformAdapter 인터페이스 활용

**User Story:** As a 개발자, I want 기존 PlatformAdapter 인터페이스를 최소한으로 변경하기를, so that 코드 안정성이 유지됩니다.

#### Acceptance Criteria

1. THE Poller SHALL PlatformAdapter.is_sold(credentials, platform_product_id)를 호출한다
2. THE SoldSyncService SHALL PlatformAdapter.delete_listing(credentials, platform_product_id)를 호출한다
3. THE System SHALL 각 플랫폼의 credentials를 PlatformAccount 테이블에서 조회한다
4. WHEN PlatformAdapter 메서드가 PlatformError를 발생시키면, THE System SHALL 이를 포착하고 적절히 처리한다
