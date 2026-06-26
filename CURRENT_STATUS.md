# 🎯 파라파라 현재 상태 (2025)

## ✅ **완료된 기능**

### **1. 사진 업로드 → S3 저장**
- ✅ S3 업로드 서비스 구현 완료
- ✅ 썸네일 생성 및 보정 처리
- 📁 `backend/app/services/media/s3.py`
- 📁 `backend/app/services/media/thumbnail.py`

### **2. 의류 카테고리·색상 자동 분류**
- ✅ AWS Rekognition 통합
- ✅ K-Fashion 모델 분류
- 📁 `backend/app/services/ai/classifier.py`

### **3. 상품 설명 자동 생성 (Claude API)**
- ✅ Claude API 통합 (Anthropic via runyour.ai)
- ✅ 상세설명 생성 로직
- 📁 `backend/app/services/ai/description.py`
- 📁 `backend/app/services/ai/pipeline.py`

### **4. FastAPI 서버 + DB**
- ✅ FastAPI 라우터 구현
  - `/api/v1/products` (상품 CRUD)
  - `/api/v1/listings` (플랫폼 등록 현황)
  - `/api/v1/platform_accounts` (플랫폼 계정 연동)
  - `/api/v1/metadata` (플랫폼 메타데이터)
  - `/api/v1/auth` (Google OAuth)
- ✅ PostgreSQL (RDS) 연결
- ✅ Alembic 마이그레이션 설정
- 📁 `backend/app/api/v1/routes/`
- 📁 `backend/app/core/database.py`

### **5. 플랫폼 자동 등록 (Playwright)**
- ✅ 플랫폼 어댑터 구조 구현
  - Bunjang (번개장터)
  - Charan (차란)
  - Daangn (당근)
  - Junggonara (중고나라)
  - Fruits
  - Ebay (부분)
- ✅ OpenClaw/Playwright 통합
- ✅ 브라우저 자동화 기반
- 📁 `backend/app/services/platform/`
- 📁 `backend/app/services/platform/forms.py` (폼 셀렉터)

### **6. 판매 완료 폴링 → 타 플랫폼 자동 삭제**
- ✅ Poller Worker 구현 (60초 주기)
- ✅ 판매 완료 감지 (각 플랫폼 폴링)
- ✅ 타 플랫폼 자동 삭제 (부분 실패 격리)
- ✅ 브라우저 재사용 최적화
- ✅ Graceful shutdown
- ✅ ECS Fargate 배포 설정
- 📁 `backend/workers/poller.py`
- 📁 `backend/app/services/automation/sold_sync.py`
- 📁 `infrastructure/ecs/poller-task-definition.json`

### **7. 미판매 상품 7일 후 10% 자동 할인**
- ✅ Auto Discount 서비스 구현
- ✅ EventBridge 스케줄 핸들러
- ✅ 가격 변경 시 모든 플랫폼 자동 반영
- ✅ Product.price 업데이트 + 플랫폼 동기화
- 📁 `backend/app/services/automation/auto_discount.py`
- 📁 `backend/workers/scheduler.py`

### **8. 상품 수정/삭제 시 플랫폼 자동 동기화**
- ✅ `DELETE /products/{id}` → 모든 플랫폼 리스팅 자동 삭제
- ✅ `PUT /products/{id}` (가격 변경) → 모든 플랫폼 가격 자동 업데이트
- ✅ `POST /listings/{listing_id}/sold` → 판매 완료 동기화 API
- 📁 `backend/app/services/automation/delete_service.py`
- 📁 `backend/app/services/automation/update_service.py`
- 📁 `backend/app/api/v1/routes/products.py`
- 📁 `backend/app/api/v1/routes/listings.py`

### **9. AWS Secrets Manager 연동**
- ✅ 플랫폼 자격증명 안전 저장
- ✅ 비동기 래핑 (asyncio.to_thread)
- 📁 `backend/app/services/secrets/manager.py`

---

## ⚠️ **미완성 / 보완 필요**

### **1. 플랫폼 폼 셀렉터 (DOM 분석 필요)**
- ⚠️ **상태**: 각 플랫폼 어댑터의 `forms.py`에서 셀렉터 빈 값
- 🔧 **필요 작업**:
  - 번개장터, 차란, 당근, 중고나라, Fruits 각 플랫폼 DOM 분석
  - 실제 CSS 셀렉터 채워넣기 (photo_input, title_input, price_input 등)
- 📁 `backend/app/services/platform/forms.py`
- 📝 **참고**: `.kiro/steering/플랫폼 input.md`에 각 플랫폼 필수 입력 필드 정의됨

### **2. 모델명 찾기 기능**
- ❌ **상태**: 미구현 (우선순위 낮음)
- 📝 **이유**: 정확도 검증 필요

### **3. Google OAuth 완전 통합**
- ⚠️ **상태**: 백엔드 라우터는 구현됨, 프론트 연동 필요
- 📁 `backend/app/api/v1/routes/auth.py`
- 🔧 **필요 작업**:
  1. Google Cloud Console에서 승인 URL 추가:
     - `https://paraparavintage.vercel.app`
     - `https://paraparavintage-pdu3c4ru7-aeongiings-projects.vercel.app`
  2. Vercel 환경변수 설정:
     - `NEXT_PUBLIC_GOOGLE_CLIENT_ID=997464628687-ko00jm7bq33o8ips0obim7g4omjs2j3e.apps.googleusercontent.com`

### **4. Ebay 플랫폼 연동**
- ⚠️ **상태**: 기본 어댑터만 구현됨 (API 연동 미완성)
- 📁 `backend/app/services/platform/ebay.py`

---

## 🚀 **배포 상태**

### **프론트엔드**
- ✅ **Vercel 배포 완료**: https://paraparavintage.vercel.app
- ✅ Framework: Next.js 16.2.9
- ⚠️ **환경변수 설정 필요** (Vercel Dashboard):
  - `NEXT_PUBLIC_API_URL` (백엔드 HTTPS URL)
  - `NEXT_PUBLIC_GOOGLE_CLIENT_ID`

### **백엔드**
- ✅ **EC2 배포**: http://100.53.237.32:8080
- ✅ **CORS 설정 완료** (Vercel URLs 추가됨)
- ❌ **CRITICAL: HTTPS 미설정**
  - 현재 HTTP만 지원
  - Mixed Content 차단 발생 (Vercel HTTPS → Backend HTTP 불가)
- 📝 **해결 방법**: `DEPLOYMENT.md` 참고
  1. Nginx + Let's Encrypt (권장)
  2. Cloudflare Tunnel
  3. Render 이전 (가장 간단)

### **데이터베이스**
- ✅ PostgreSQL (RDS) 구축 완료
- ✅ DATABASE_URL 설정됨

### **인프라**
- ✅ ECS Fargate Task Definition (Poller)
- ✅ IAM 정책 (Secrets Manager, CloudWatch)
- 📁 `infrastructure/ecs/poller-task-definition.json`
- 📁 `infrastructure/iam/poller-policy.json`
- 📁 `infrastructure/README.md`

---

## 🐛 **현재 이슈**

### **1. Mixed Content 차단 (회원가입 에러 원인)**
```
Vercel (HTTPS) → Backend (HTTP)
    ❌ 브라우저가 보안상 차단!
```

**브라우저 콘솔 에러**:
```
Mixed Content: The page at 'https://paraparavintage.vercel.app' 
was loaded over HTTPS, but requested an insecure XMLHttpRequest endpoint 
'http://100.53.237.32:8080'. This request has been blocked.
```

**해결 방법**:
- 백엔드에 HTTPS 설정 필수 (3가지 방법 중 선택)
- 상세 가이드: `DEPLOYMENT.md` 참고

### **2. 플랫폼 셀렉터 미완성**
- 각 플랫폼 DOM 분석 후 `forms.py`에 실제 셀렉터 채워야 함
- 현재는 빈 문자열로 되어 있어 실제 업로드 불가

---

## 📋 **다음 단계 (우선순위)**

### **🔥 최우선 (배포 완성)**
1. **백엔드 HTTPS 설정**
   - 방법 선택: Nginx / Cloudflare / Render
   - `DEPLOYMENT.md` 가이드 따라 진행
2. **Vercel 환경변수 설정**
   - `NEXT_PUBLIC_API_URL` (HTTPS URL)
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID`
3. **Google OAuth 승인 URL 추가**
4. **회원가입/로그인 테스트**

### **⚡ 높음 (핵심 기능)**
5. **플랫폼 셀렉터 채우기**
   - 번개장터, 차란, 당근 우선
   - DOM 분석 후 `forms.py` 업데이트
6. **Poller Worker ECS 배포**
   - Task Definition 이미 준비됨
   - ECS 클러스터에 배포
7. **Auto Discount EventBridge 설정**
   - 매일 자정 실행

### **📝 중간 (개선)**
8. **에러 로깅 강화** (CloudWatch)
9. **모니터링 대시보드** (CloudWatch / Grafana)
10. **API 문서 개선** (FastAPI Swagger)

### **🎁 낮음 (추후)**
11. **모델명 찾기 기능** (정확도 검증 필요)
12. **Ebay 연동 완성**
13. **결제 연동** (StepPay Power)

---

## 🛠️ **기술 스택**

### **Frontend**
- Next.js 16.2.9 (App Router)
- React
- TypeScript

### **Backend**
- FastAPI (Python)
- Pydantic (검증)
- SQLAlchemy (ORM)
- Alembic (마이그레이션)
- Playwright (브라우저 자동화)

### **Database**
- PostgreSQL (RDS)
- JSONB 활용

### **AI/ML**
- AWS Rekognion (이미지 분석)
- K-Fashion 모델 (카테고리 분류)
- Claude API (설명 생성)

### **Infrastructure**
- AWS S3 (사진 저장)
- AWS Secrets Manager (자격증명)
- AWS ECS Fargate (Poller Worker)
- AWS EventBridge (Auto Discount)
- Vercel (프론트 배포)
- EC2 (백엔드 배포)

---

## 📞 **팀 공유**

### **백엔드 담당자 확인 필요**
1. ✅ CORS 설정 완료 (Vercel URLs 추가됨)
2. ✅ Git push 완료 → **서버에서 pull 후 재시작 필요**
3. ❌ HTTPS 설정 필요 → `DEPLOYMENT.md` 참고

### **프론트엔드 담당자 확인 필요**
1. ⚠️ Vercel 환경변수 설정 (Dashboard에서)
2. ⚠️ Google OAuth 승인 URL 추가 (Google Console)
3. ✅ CORS 문제 해결됨 (백엔드 서버 재시작 후)

### **DevOps 담당자 확인 필요**
1. ❌ 백엔드 HTTPS 설정 (3가지 방법 중 선택)
2. ⚠️ Poller Worker ECS 배포
3. ⚠️ EventBridge 스케줄 설정

---

## 🔗 **링크**

- **프론트**: https://paraparavintage.vercel.app
- **백엔드 (현재)**: http://100.53.237.32:8080
- **API 문서**: http://100.53.237.32:8080/docs
- **GitHub**: https://github.com/aeongiing/Primero
- **Google Console**: https://console.cloud.google.com/
- **Vercel Dashboard**: https://vercel.com/aeongiings-projects/paraparavintage

---

## ✅ **완료 체크리스트**

### **코드 구현**
- [x] 사진 업로드 → S3
- [x] AI 카테고리·색상 분류
- [x] 상품 설명 자동 생성
- [x] 썸네일 보정
- [x] FastAPI 서버 + DB
- [x] 플랫폼 자동 등록 (어댑터 구조)
- [x] 판매 완료 폴링 → 자동 삭제
- [x] 미판매 7일 후 10% 할인
- [x] 상품 수정/삭제 시 플랫폼 동기화
- [x] AWS Secrets Manager 연동

### **인프라**
- [x] PostgreSQL (RDS)
- [x] S3 버킷
- [x] ECS Task Definition (Poller)
- [x] IAM 정책
- [ ] ECS 배포 (실행)
- [ ] EventBridge 스케줄 (실행)
- [ ] 백엔드 HTTPS 설정

### **배포**
- [x] 프론트엔드 Vercel 배포
- [x] 백엔드 EC2 배포
- [x] CORS 설정
- [ ] HTTPS 설정 (CRITICAL)
- [ ] Vercel 환경변수 설정
- [ ] Google OAuth 승인 URL

### **테스트**
- [ ] 회원가입/로그인
- [ ] 상품 업로드 플로우
- [ ] 플랫폼 자동 등록
- [ ] 판매 완료 동기화
- [ ] 자동 할인

---

**마지막 업데이트**: 2025년 (Git commit: ff142ec)
