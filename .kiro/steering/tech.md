---
inclusion: always
---

# 파라파라 — 기술 스택 & 규칙

## 스택
- 프론트엔드: Next.js (App Router) · React · TypeScript
- 백엔드: FastAPI (Python) · Pydantic
- DB: PostgreSQL (JSONB 활용)
- 사진: AWS S3
- 이미지 분석: AWS Rekognition / K-Fashion
- AI 생성: Claude API (상세설명·후킹멘트·모델명 추론)
- 플랫폼 자동화: OpenClaw
- 스케줄링: APScheduler / Celery + Redis (할인·폴링)
- 인증(추후): Google OAuth

## 아키텍처 규칙
- 4레이어: 표현(Next.js) → API(FastAPI 라우터) → 도메인 코어 → 인프라/어댑터.
- **도메인 코어는 외부 서비스에 의존하지 않는다.** S3·Rekognition·Claude·OpenClaw는 어댑터로 캡슐화한다. 코어는 순수 로직으로 유지해 속성 기반 테스트 대상으로 둔다.
- 외부 호출(분석·보정·발행·폴링)은 백그라운드 작업으로 처리하고 API는 작업 ID를 즉시 반환한다.

## 비밀 정보 (엄수)
- Claude API 키·플랫폼 자격증명은 `시크릿_관리_모듈`을 통해서만 로드한다.
- 소스 저장소에 평문 키 금지. `.env.example`만 커밋한다.
- 로그·오류 메시지에 키 값 금지 — 키 이름만 참조한다.
- 기획서에 노출됐던 Claude 키는 **폐기·재발급 대상**이다.

## 테스트
- PBT: 백엔드 **Hypothesis**, 프론트 **fast-check**. 각 속성 테스트 **최소 100회** 반복.
- 태그 형식: `Feature: parapara-upload-automation, Property {번호}`.
- 외부 의존은 모킹. UI는 스냅샷, 외부 연동은 통합 테스트.

## 공통 오류 응답 형식
```json
{ "error_code": "VALIDATION_ERROR", "message": "설명(시크릿 미포함)", "details": {} }
```
