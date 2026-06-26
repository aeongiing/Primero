---
inclusion: always
---

# 파라파라 — 프로젝트 구조

```
/
├── backend/    FastAPI 서버 + 도메인 코어 + 어댑터 + DB 마이그레이션
├── frontend/   Next.js (업로드 플로우 · 사진 정렬 · 상세페이지)
└── .kiro/
    ├── specs/parapara-upload-automation/   requirements · design · tasks
    ├── steering/                           product · tech · structure · platform-upload
    ├── settings/mcp.json                   platform-docs MCP
    └── powers/step-pay/                    결제(StepPay) 연동 power 스캐폴드 (추후)
```

## 백엔드 레이어 배치 규칙
- `domain/` — 순수 로직(표준_상품 검증, 사진 정렬, 매핑, 할인, 동기화). 외부 import 금지.
- `adapters/` — S3 · Rekognition · Claude · OpenClaw · DB 연동.
- `api/` — FastAPI 라우터. 검증 → 코어 호출 → 직렬화.
- 매핑 config는 코드가 아닌 **선언적 설정**으로 둔다. 신규 플랫폼은 config 추가만으로 지원.

## 네이밍
- 도메인 용어는 spec의 Glossary를 따른다(표준_상품, 외부_플랫폼, 플랫폼_매핑_엔진 등).
- 사진 역할 enum: `front/closeup/back/detail/stain/tag` (앞/확대/뒤/디테일/오염/태그).
- 판매 상태 enum: `draft/listed/sold/taken_down`.
