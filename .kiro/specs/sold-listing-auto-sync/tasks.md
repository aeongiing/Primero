# Implementation Plan: Sold Listing Auto Sync

## Overview

이 구현 계획은 판매 완료 감지 폴링 및 타 플랫폼 자동 삭제 기능을 단계별로 구현합니다. SSOT 원칙에 따라 Product를 중심으로 모든 플랫폼 리스팅을 동기화하며, 부분 실패 격리를 통해 한 플랫폼의 오류가 다른 플랫폼에 영향을 주지 않도록 합니다.

핵심 구현 순서:
1. 데이터 모델 및 스키마 확립
2. SoldSyncService 핵심 로직 구현
3. PlatformAdapter 인터페이스 확장
4. Poller Worker 구현
5. AWS Secrets Manager 연동
6. ECS Fargate 배포 설정

## Tasks

- [ ] 1. 데이터 모델 및 스키마 설정
  - [x] 1.1 Sale 모델 확인 및 필요 시 필드 추가
    - `app/models/sale.py`에서 Sale 모델 확인
    - 필요한 필드: id, product_id, listing_id, platform, sold_at
    - 인덱스 추가: `product_id`, `listing_id`
    - _Requirements: 2.4_
  
  - [x] 1.2 Listing 모델 상태 전이 확인
    - `app/models/listing.py`에서 ListingStatus enum 확인
    - `pending`, `active`, `sold`, `removed` 상태 존재 확인
    - 필요 시 `removed` 상태 추가
    - _Requirements: 3.3_
  
  - [-] 1.3 데이터베이스 인덱스 최적화
    - `idx_listing_status_active` 인덱스 생성 (WHERE status = 'active')
    - `idx_listing_product_id` 인덱스 확인
    - `idx_product_status` 인덱스 확인
    - Alembic 마이그레이션 스크립트 작성
    - _Requirements: 1.1_

- [ ] 2. Credentials Management 구현
  - [-] 2.1 AWS Secrets Manager 클라이언트 구현
    - `app/services/secrets/manager.py` 생성
    - `load_credentials(credential_key: str) -> Credentials` 함수 구현
    - boto3로 `get_secret_value` 호출
    - JSON 파싱하여 Credentials 객체 반환
    - 오류 처리: SecretNotFound, AccessDenied
    - _Requirements: 8.3_
  
  - [ ]* 2.2 Credentials Manager 단위 테스트 작성
    - Mock boto3 클라이언트로 정상 케이스 테스트
    - SecretNotFound 시 적절한 예외 발생 확인
    - AccessDenied 시 적절한 예외 발생 확인
    - 로그에 credential 값 노출 안 됨 확인
    - _Requirements: 5.2, 5.4_

- [ ] 3. Checkpoint - 기본 인프라 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. SoldSyncService 핵심 로직 구현
  - [ ] 4.1 SyncResult 데이터 클래스 정의
    - `app/services/automation/sold_sync.py`에 SyncResult 추가
    - 필드: product_id, sold_listing_id, deleted_count, failed_count, failed_platforms
    - _Requirements: 4.4_
  
  - [ ] 4.2 sync_sold 메서드 기본 구조 작성
    - 함수 시그니처: `async def sync_sold(db: AsyncSession, product_id: UUID, sold_listing_id: UUID) -> SyncResult`
    - 동시성 체크: Product.status가 이미 sold면 조기 반환
    - _Requirements: 7.1, 7.2_
  
  - [ ] 4.3 Product/Listing/Sale 트랜잭션 업데이트 구현
    - Product.status를 sold로 변경
    - Listing.status를 sold로 변경 (sold_listing_id)
    - Sale 레코드 생성 (product_id, listing_id, platform, sold_at)
    - 단일 트랜잭션으로 커밋
    - _Requirements: 2.1, 2.2, 2.3, 7.3_
  
  - [ ] 4.4 나머지 플랫폼 리스팅 삭제 로직 구현
    - 나머지 active 리스팅 조회 (sold_listing 제외)
    - PlatformRegistry에서 어댑터 가져오기
    - 각 리스팅마다 try-except로 격리
    - `adapter.delete_listing()` 호출
    - 성공 시: Listing.status = removed, deleted_count++
    - 실패 시: 로깅, failed_count++, failed_platforms 추가
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3_
  
  - [ ]* 4.5 SoldSyncService 단위 테스트 작성
    - Mock DB와 Mock PlatformAdapter 사용
    - 정상 시나리오: 모든 리스팅 삭제 성공
    - 동시성 시나리오: 이미 sold인 경우 조기 반환
    - 부분 실패 시나리오: 일부 플랫폼 실패해도 나머지 계속
    - 트랜잭션 원자성: Product/Listing/Sale 동시 커밋
    - SyncResult 반환값 검증
    - _Requirements: 2.1, 2.2, 2.3, 3.3, 4.1, 4.4, 7.1, 7.3_

- [ ] 5. Checkpoint - SoldSyncService 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. PlatformAdapter 인터페이스 확장
  - [ ] 6.1 PlatformAdapter 베이스 클래스에 is_sold 메서드 확인
    - `app/services/platform/base.py`에서 is_sold 메서드 존재 확인
    - 필요 시 추상 메서드로 추가
    - 시그니처: `async def is_sold(self, credentials: Credentials, platform_product_id: str) -> bool`
    - _Requirements: 8.1_
  
  - [ ] 6.2 PlatformAdapter 베이스 클래스에 delete_listing 메서드 확인
    - `app/services/platform/base.py`에서 delete_listing 메서드 존재 확인
    - 필요 시 추상 메서드로 추가
    - 시그니처: `async def delete_listing(self, credentials: Credentials, platform_product_id: str) -> None`
    - _Requirements: 8.2_
  
  - [ ] 6.3 FormPlatformAdapter에 is_sold 구현 확인 및 개선
    - `app/services/platform/base.py`의 FormPlatformAdapter 확인
    - spec.listing_url_template, spec.sold_selector, spec.sold_marker 활용
    - 페이지 로드 → 셀렉터로 텍스트 추출 → sold_marker 포함 여부 반환
    - PlatformError 처리 (셀렉터 미발견, 타임아웃)
    - _Requirements: 1.2, 8.4_
  
  - [ ] 6.4 FormPlatformAdapter에 delete_listing 구현 확인 및 개선
    - spec.manage_url_template, spec.delete_selector, spec.delete_confirm_selector 활용
    - 페이지 로드 → 삭제 버튼 클릭 → 확인 버튼 클릭
    - PlatformError 처리
    - _Requirements: 3.2, 8.4_
  
  - [ ] 6.5 번개장터/당근/차란 플랫폼 스펙 완성
    - `app/services/platform/bunjang.py`: listing_url_template, sold_selector, sold_marker, manage_url_template, delete_selector, delete_confirm_selector 추가
    - `app/services/platform/karrot.py`: 동일 필드 추가
    - `app/services/platform/charan.py`: 동일 필드 추가
    - DOM 캡처를 통해 실제 셀렉터 확인 (스크립트 활용)
    - _Requirements: 1.2, 3.2_
  
  - [ ]* 6.6 PlatformAdapter 단위 테스트 작성
    - Mock BrowserPage로 is_sold/delete_listing 시뮬레이션
    - 셀렉터 미발견 시 PlatformError 발생 확인
    - sold_marker 정확히 매칭하는지 확인
    - delete 성공 시나리오 확인
    - _Requirements: 1.2, 3.2, 8.4_

- [ ] 7. Checkpoint - PlatformAdapter 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Poller Worker 구현
  - [ ] 8.1 Poller 기본 구조 작성
    - `workers/poller.py` 파일 생성
    - 환경변수: POLLING_INTERVAL_SECONDS (기본값 60)
    - DATABASE_URL, AWS_REGION 등 환경변수 로드
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [ ] 8.2 poll_once 함수 구현
    - DB에서 `Listing.status = active` 조회 (JOIN Product, PlatformAccount)
    - Product.status != sold 필터링
    - 플랫폼별로 그룹핑
    - 각 리스팅에 대해 `adapter.is_sold()` 호출
    - True 반환 시 `SoldSyncService.sync_sold()` 호출
    - 플랫폼별 오류는 로깅 후 다음 플랫폼 계속
    - _Requirements: 1.1, 1.2, 1.3, 1.5_
  
  - [ ] 8.3 브라우저 인스턴스 재사용 로직 추가
    - 플랫폼별로 단일 BrowserAutomation 인스턴스 생성
    - storage_state 파일 활용하여 로그인 세션 재사용
    - 폴링 사이클 완료 후 브라우저 정리
    - _Requirements: 1.1, 1.2_
  
  - [ ] 8.4 run 함수 및 graceful shutdown 구현
    - 60초 주기 폴링 루프
    - signal handler (SIGTERM, SIGINT) 등록
    - shutdown_event.set() 시 현재 사이클 완료 후 종료
    - 로깅: 폴링 사이클 시작/완료, 판매 감지
    - _Requirements: 1.4, 6.4_
  
  - [ ]* 8.5 Poller 통합 테스트 작성
    - Mock DB, Mock SoldSyncService
    - 브라우저 인스턴스 재사용 확인
    - 플랫폼별 오류 격리 확인
    - Graceful shutdown 동작 확인
    - _Requirements: 1.1, 1.4, 1.5, 6.4_

- [ ] 9. Checkpoint - Poller Worker 검증
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. 로깅 및 에러 처리 강화
  - [ ] 10.1 구조화된 로그 메시지 작성
    - INFO: 폴링 사이클 시작/완료, 판매 감지, 삭제 성공
    - WARNING: 개별 플랫폼 오류
    - ERROR: 데이터베이스 오류, Secrets Manager 오류
    - 로그 포맷: product_id, listing_id, platform 포함
    - _Requirements: 5.1_
  
  - [ ] 10.2 로그 sanitization 구현
    - credential 값(username/password/token) 로그 노출 금지
    - credential_key만 참조
    - PlatformError 메시지에 자격증명 미포함 확인
    - 필요 시 logging.Filter 구현
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [ ] 10.3 Sentry 연동 설정
    - SENTRY_DSN 환경변수 설정
    - Sentry SDK 초기화
    - 민감 정보 필터링 설정
    - _Requirements: 5.1_

- [ ] 11. 배포 설정 및 인프라 구성
  - [ ] 11.1 Dockerfile 업데이트
    - Playwright 및 Chromium 설치
    - `playwright install chromium`
    - `playwright install-deps`
    - 한글 폰트 설치 (fonts-nanum, fonts-noto-cjk)
    - _Requirements: 6.1_
  
  - [ ] 11.2 환경변수 및 설정 파일 작성
    - `.env.example`에 Poller 관련 환경변수 추가
    - POLLING_INTERVAL_SECONDS, BROWSER_HEADLESS, AWS_REGION, SECRETS_MANAGER_PREFIX
    - _Requirements: 6.2_
  
  - [ ] 11.3 ECS Task Definition 작성
    - `infrastructure/ecs/poller-task-definition.json` 생성
    - Fargate 호환, CPU 512, Memory 1024
    - command: `["python", "-m", "workers.poller"]`
    - environment 및 secrets 설정
    - CloudWatch Logs 구성
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [ ] 11.4 IAM 정책 문서 작성
    - Secrets Manager GetSecretValue 권한
    - Resource: `parapara/platform/*`
    - `infrastructure/iam/poller-policy.json` 생성
    - _Requirements: 8.3_

- [ ]* 12. 통합 테스트 및 엔드투엔드 검증
  - [ ]* 12.1 엔드투엔드 시나리오 테스트 작성
    - 테스트 DB에 Product/Listing 생성 (3개 플랫폼)
    - Mock Browser로 한 플랫폼만 sold 반환
    - Poller 실행
    - Product.status = sold 확인
    - Sale 레코드 생성 확인
    - 나머지 2개 Listing status = removed 확인
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_
  
  - [ ]* 12.2 실제 플랫폼 연동 테스트 (수동 실행)
    - 테스트 계정으로 실제 등록/삭제 수행
    - 셀렉터 정확성 검증
    - 로그인 세션 재사용 확인
    - 이 테스트는 CI/CD에서 건너뛰기
    - _Requirements: 1.2, 3.2_

- [ ] 13. 최종 검증 및 문서화
  - [ ] 13.1 README 및 운영 가이드 작성
    - Poller 실행 방법 (로컬, ECS)
    - 환경변수 설정 가이드
    - 트러블슈팅 가이드
    - 삭제 실패 시 수동 복구 방법
  
  - [ ] 13.2 모니터링 및 알림 설정 계획
    - CloudWatch Logs 쿼리 예시
    - 폴링 주기당 처리 시간 메트릭
    - 삭제 성공/실패율 추적
    - 플랫폼별 오류율 대시보드

- [ ] 14. Final Checkpoint - 전체 시스템 검증
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- 각 작업은 특정 requirements를 참조하여 traceability 확보
- Checkpoint tasks는 incremental validation을 위해 주요 단계마다 포함
- Unit tests와 integration tests로 충분히 검증 (PBT 미적용)
- 부분 실패 격리가 핵심: 한 플랫폼 실패가 다른 플랫폼에 영향 없음
- SSOT 원칙: Product 상태가 모든 동기화의 기준
- 비밀 정보 보호: 로그/오류 메시지에 자격증명 절대 노출 금지

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["1.3", "2.1"] },
    { "id": 2, "tasks": ["2.2", "4.1"] },
    { "id": 3, "tasks": ["4.2", "6.1", "6.2"] },
    { "id": 4, "tasks": ["4.3", "6.3", "6.4"] },
    { "id": 5, "tasks": ["4.4", "6.5"] },
    { "id": 6, "tasks": ["4.5", "6.6", "8.1"] },
    { "id": 7, "tasks": ["8.2", "10.1"] },
    { "id": 8, "tasks": ["8.3", "10.2"] },
    { "id": 9, "tasks": ["8.4", "10.3", "11.1"] },
    { "id": 10, "tasks": ["8.5", "11.2", "11.3", "11.4"] },
    { "id": 11, "tasks": ["12.1", "12.2"] },
    { "id": 12, "tasks": ["13.1", "13.2"] }
  ]
}
```
