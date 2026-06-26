# 인증 + 인프라 인수인계 (RDS 방향)

정예원(프론트)이 Google 로그인/회원가입과 AI 분석 연동을 구현한 뒤, **DB(RDS) 연결과
배포 환경 정리**를 백엔드/인프라 담당에게 넘기는 문서.

## 1. 지금까지 구현·검증된 것

### 인증 (Google OAuth → 자체 JWT)
- `app/api/v1/routes/auth.py`
  - `POST /auth/google`: Google `id_token` 검증(`google-auth`) → 사용자 **upsert(첫 로그인=회원가입)** → `create_access_token(str(user.id))` 로 JWT 발급.
  - `GET /auth/me`: JWT → 사용자 반환.
- `app/core/config.py`: `google_client_id` 추가. 프론트와 **동일한 Client ID** 사용.
- 프론트 `src/app/login/page.tsx`: Google Identity Services 버튼 → `googleLogin()` → `localStorage("parapara_token")` 저장 → 홈 이동. (`src/lib/api.ts` 가 모든 요청에 `Authorization: Bearer` 자동 첨부)
- **검증 상태**: 더미 토큰 → `401`(정상 거절), Client ID 로드 OK. **DB만 붙으면 실제 로그인 동작.**

### AI 분석
- `POST /products/analyze`: S3 없이 **이미지 바이트를 바로 Claude로** 전송(인증 불필요). 실제 사진으로 카테고리·색상·브랜드(태그)·설명 생성 검증 완료.
- 현재 **Anthropic 직접 API**(`ANTHROPIC_API_KEY`, 선택적 `ANTHROPIC_BASE_URL`) 사용. `BEDROCK_MODEL_ID`는 선언만 돼 있고 미사용.

## 2. RDS 연결로 넘길 때 할 일 (중요)

1. **`DATABASE_URL` 을 실제 RDS 로 교체** (`backend/.env`)
   ```
   DATABASE_URL=postgresql+asyncpg://<user>:<pw>@<rds-endpoint>:5432/<db>
   ```
   - 현재 값은 기본 placeholder(`user:password@localhost`)라 **인증 실패**한다.
   - 드라이버는 반드시 `postgresql+asyncpg`(async).

2. **테이블 생성 — 레포에 마이그레이션이 없다!**
   - `alembic` 은 requirements 에 있으나 `migrations/` 폴더·버전이 없음. `create_all` 호출부도 없음.
   - 둘 중 하나 필요:
     - (간단) 부트스트랩 스크립트로 `Base.metadata.create_all` 1회 실행해 `users / products / product_images / listings / platform_accounts / sales` 생성. (모델: `app/models/*`)
     - (정석) `alembic init` + 초기 리비전 작성 후 `alembic upgrade head`.

3. **`greenlet` 의존성** — SQLAlchemy 비동기에 필수인데 빠져 있었음. `requirements.txt` 에 `greenlet==3.5.3` 추가 완료. (RDS·로컬 무관하게 `pip install -r requirements.txt` 재실행 필요)

4. **AWS 자격증명** — S3·(선택)Bedrock·Rekognition 은 배포 서버의 **IAM 역할**로 접근. 로컬엔 키가 없으니 `.env` 의 `AWS_ACCESS_KEY_ID/SECRET` 는 **비워둠**(채우면 IAM 역할 폴백을 막아 오히려 실패).

## 3. 필요한 환경변수 (backend/.env)

| 키 | 용도 | 비고 |
|---|---|---|
| `DATABASE_URL` | RDS 연결 | `postgresql+asyncpg://...` |
| `GOOGLE_CLIENT_ID` | Google id_token 검증 | 프론트와 동일 |
| `JWT_SECRET` | JWT 서명 | 운영 비밀값으로 |
| `ANTHROPIC_API_KEY` | Claude(직접 API) | 동작 확인됨 |
| `ANTHROPIC_MODEL` | 모델명 | 예: `claude-sonnet-4-5-20250929` |
| `ANTHROPIC_BASE_URL` | 게이트웨이(선택) | 없으면 기본 endpoint |
| `AWS_REGION` / `S3_BUCKET` | S3 | 서버 IAM 역할로 접근 |
| `BEDROCK_MODEL_ID` | (선택) Bedrock 전환 시 | 현재 미사용 |

프론트 `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=<백엔드 URL>
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<GOOGLE_CLIENT_ID 와 동일>
```

## 4. Bedrock 으로 전환하려면 (선택)
- `classifier.py` 의 `_invoke_content` 를 `boto3.client("bedrock-runtime")` 의 `converse`/`invoke_model`(modelId=`BEDROCK_MODEL_ID`) 호출로 교체.
- 별도 Anthropic 키 불필요 → AWS IAM 으로 인증. 단 **Bedrock 콘솔에서 Claude 모델 액세스 활성화** 필요.
- 현재는 Anthropic 직접 API 가 동작하므로 필수는 아님.

## 5. CORS / 배포
- `app/main.py` CORS: 로컬 dev 포트(`localhost:*`) 허용 추가됨. 배포 시 **실제 프론트 오리진으로 좁힐 것**.

## 6. 열린 항목 (TODO)
- [ ] RDS `DATABASE_URL` 설정 + 테이블 생성(마이그레이션 도입)
- [ ] 로그인 end-to-end 테스트(브라우저 Google 로그인 → JWT → `/products` 등)
- [ ] `POST /products` 의 `platforms` 활성값(`bunjang`,`junggonara`)과 프론트 선택 UX 정합
- [ ] 이미지: 프론트 표시용 S3 presigned URL(또는 공개 URL) 응답 추가 (ProductOut 에 이미지 URL 없음)
- [ ] (선택) Claude Bedrock 전환 여부 결정
