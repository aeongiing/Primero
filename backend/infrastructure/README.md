# Parapara 판매 완료 폴링 배포 가이드

## 개요
판매 완료 자동 동기화 기능의 배포 설정 파일입니다.

## 구성 요소

### 1. ECS Fargate Poller
- **파일**: `ecs/poller-task-definition.json`
- **역할**: 60초마다 active 리스팅을 폴링하여 판매 완료 감지
- **리소스**: CPU 512, Memory 1024MB
- **로그**: CloudWatch Logs `/ecs/parapara-poller`

### 2. IAM 정책
- **파일**: `iam/poller-policy.json`
- **권한**:
  - Secrets Manager: 플랫폼 자격증명 및 DB URL 조회
  - CloudWatch Logs: 로그 쓰기

## 배포 순서

### 1. Docker 이미지 빌드 및 푸시
```bash
cd backend
docker build -t parapara-backend .
docker tag parapara-backend:latest ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/parapara-backend:latest
docker push ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/parapara-backend:latest
```

### 2. IAM Role 생성
```bash
# Task Role 생성
aws iam create-role \
  --role-name parapara-poller-task-role \
  --assume-role-policy-document file://iam/trust-policy.json

# 정책 연결
aws iam put-role-policy \
  --role-name parapara-poller-task-role \
  --policy-name parapara-poller-policy \
  --policy-document file://iam/poller-policy.json
```

### 3. Secrets Manager 설정
```bash
# DB URL 등록
aws secretsmanager create-secret \
  --name parapara/database-url \
  --secret-string "postgresql+asyncpg://user:password@hostname:5432/primero"

# 플랫폼 자격증명 등록 (예시)
aws secretsmanager create-secret \
  --name parapara/platform/user123/bunjang \
  --secret-string '{"username":"user123","password":"secret"}'
```

### 4. ECS Task Definition 등록
```bash
# ACCOUNT_ID 치환
sed -i 's/ACCOUNT_ID/123456789012/g' ecs/poller-task-definition.json

# Task Definition 등록
aws ecs register-task-definition \
  --cli-input-json file://ecs/poller-task-definition.json
```

### 5. ECS Service 생성
```bash
aws ecs create-service \
  --cluster parapara-cluster \
  --service-name parapara-poller \
  --task-definition parapara-poller \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## 모니터링

### CloudWatch Logs 확인
```bash
aws logs tail /ecs/parapara-poller --follow
```

### 주요 로그 패턴
- `Polling cycle started` - 폴링 시작
- `Sold detected` - 판매 완료 감지
- `Removed listing` - 타 플랫폼 삭제 성공
- `Failed to delete listing` - 삭제 실패 (재시도 대기)

### 메트릭
- 폴링 주기당 처리 시간
- 삭제 성공/실패율
- 플랫폼별 오류율

## 트러블슈팅

### Poller가 시작되지 않음
- ECS Task 로그 확인: `aws ecs describe-tasks`
- DB 연결 확인: Secrets Manager의 DATABASE_URL 검증
- IAM 권한 확인: Task Role에 SecretsManager 권한 있는지

### 삭제 실패가 반복됨
- 플랫폼 자격증명 만료 확인
- 플랫폼 셀렉터 변경 여부 확인 (DOM 캡처 재수행)
- CloudWatch Logs에서 PlatformError 메시지 확인

### 성능 문제 (폴링 느림)
- 브라우저 인스턴스 재사용 확인
- Active 리스팅 개수 확인 (너무 많으면 분산 배포 고려)
- ECS Task 리소스 증가 (CPU/Memory)

## 환경변수

| 변수 | 기본값 | 설명 |
|-----|--------|------|
| `POLLING_INTERVAL_SECONDS` | 60 | 폴링 주기 (초) |
| `BROWSER_HEADLESS` | true | 헤드리스 브라우저 사용 |
| `SECRETS_MANAGER_PREFIX` | parapara/platform | 자격증명 키 접두사 |

## 비용 추정

### ECS Fargate (1개 태스크)
- CPU 0.5 vCPU: $0.04048/시간
- Memory 1GB: $0.004445/시간
- **월 비용**: 약 $32

### 추가 비용
- CloudWatch Logs: 로그 양에 따라
- Secrets Manager: 시크릿 개수 × $0.40/월

## 참고
- Requirements: `.kiro/specs/sold-listing-auto-sync/requirements.md`
- Design: `.kiro/specs/sold-listing-auto-sync/design.md`
- Tasks: `.kiro/specs/sold-listing-auto-sync/tasks.md`
