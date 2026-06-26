# 파라파라 백엔드 API 스키마

현재 코드(`app/schemas`, `app/api/v1/routes`, `app/models`) 기준으로 정리한 API 계약 문서.
작업 1(analyze·등록·목록 스펙 합의)의 기준 문서로 사용한다.

- **Base URL**: `/api/v1`
- **인증**: `auth/google` 와 `products/analyze` 를 제외한 모든 엔드포인트는 `Authorization: Bearer <JWT>` 필요.
- **상태**: ✅ 구현 완료 · 🚧 스켈레톤(미구현) · 담당자 표기.

---

## 1. 공통

### 1.1 공통 오류 응답 (steering: tech.md)

```json
{ "error_code": "VALIDATION_ERROR", "message": "설명(시크릿 미포함)", "details": {} }
```

> 참고: 현재 라우트는 FastAPI 기본 오류 형식(`{"detail": ...}`)을 사용한다. 작업 1에서 위 공통 형식으로 통일할지 합의 필요.

### 1.2 Enum

**ProductStatus** (`status` 필드)

| 값 | 의미 |
|----|------|
| `draft` | 등록 직후, 플랫폼 미발행 |
| `listing` | 발행 진행 중 |
| `listed` | 플랫폼 등록 완료 |
| `sold` | 판매 완료 |
| `unlisted` | 내림 처리됨 |

**ListingStatus** (플랫폼별 등록물)

| 값 | 의미 |
|----|------|
| `pending` | 발행 대기 |
| `active` | 등록 활성 |
| `sold` | 해당 플랫폼에서 판매 |
| `removed` | 삭제됨 |

**ProductImage.order** (사진 역할, 0부터)

| order | 역할 |
|-------|------|
| 0 | 앞 (front) |
| 1 | 확대 (closeup) |
| 2 | 뒤 (back) |
| 3 | 디테일 (detail) |
| 4 | 오염 (stain) |
| 5 | 태그 (tag) |

---

## 2. 인증 — `/auth`  · 담당: 이여원(추후)

### `POST /auth/google` 🚧
구글 `id_token` 검증 → 사용자 upsert → 자체 JWT 발급.

요청 `GoogleLoginRequest`
```json
{ "id_token": "string" }
```

응답 `TokenResponse`
```json
{ "access_token": "string", "token_type": "bearer" }
```

### `GET /auth/me` 🚧
응답 `UserOut`
```json
{ "id": "uuid", "email": "string", "created_at": "datetime" }
```

---

## 3. 상품 — `/products`

### `POST /products/analyze` 🚧 · 담당: 윤채린(백A)
이미지 업로드 → 분석/설명 생성. **multipart/form-data**, 필드명 `images` (복수 파일).

응답 `AIAnalysisResult`
```json
{
  "title": "string",
  "brand": "string",
  "category": "string",
  "description": "string",
  "condition": 0,
  "size": "string | null",
  "chest": 0,
  "total_length": 0,
  "waist": 0,
  "hip": 0,
  "rise": 0,
  "colors": ["string"],
  "material": "string"
}
```
> `condition` 은 정수(1~10 척도). `chest/total_length/waist/hip/rise` 는 cm 실측(없으면 null).

### `POST /products` ✅ · 담당: 이여원(백B)
표준_상품 생성 → DB 저장(상태 `draft`). 플랫폼 발행(작업 7)은 별도 단계.

요청 `ProductCreate`
```json
{
  "title": "string",
  "brand": "string",
  "description": "string",
  "category": "string",
  "condition": 8,
  "price": 45000,
  "size": "L",
  "colors": ["블랙", "차콜"],
  "materials": ["면", "폴리에스터"],
  "chest": null,
  "total_length": null,
  "waist": null,
  "hip": null,
  "rise": null,
  "platforms": ["karrot", "bunjang"]
}
```
검증: `condition` 1~10, `price` > 0. `platforms` 는 발행 대상(작업 7에서 사용).
`colors`/`materials` 는 정규값(차란 기준) 리스트. 생략 시 빈 배열. 플랫폼별 개수
제약(예: 차란 소재 최대 4)은 저장 시점이 아니라 매핑 엔진(작업 7)에서 절단한다.

응답 `201` `ProductOut` (아래 4.1).

### `GET /products?status=<ProductStatus>` ✅ · 담당: 이여원(백B)
현재 사용자 상품 목록(최신순). `status` 선택 필터.
응답 `200` `ProductOut[]`.

### `GET /products/{product_id}` ✅
응답 `200` `ProductOut` · 미소유/없음 `404`.

### `PATCH /products/{product_id}` ✅
부분 수정. 요청 `ProductUpdate`
```json
{ "title": "string?", "description": "string?", "price": 39000, "condition": 8 }
```
검증: `price` > 0, `condition` 1~10. 전달한 필드만 갱신.
응답 `200` `ProductOut`.

### `DELETE /products/{product_id}` ✅
표준_상품 + 종속 이미지/리스팅 DB 삭제(cascade). 플랫폼 측 삭제는 작업 8.
응답 `204`.

---

## 4. 상품 스키마

### 4.1 `ProductOut`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "string",
  "brand": "string",
  "description": "string",
  "category": "string",
  "condition": 8,
  "price": 45000,
  "status": "draft",
  "size": "L | null",
  "colors": ["블랙", "차콜"],
  "materials": ["면", "폴리에스터"],
  "chest": null,
  "total_length": null,
  "waist": null,
  "hip": null,
  "rise": null,
  "created_at": "datetime",
  "images": [ { "id": "uuid", "s3_key": "string", "order": 0 } ]
}
```
> `ProductOut` 에는 플랫폼 등록 현황이 포함되지 않는다. 리스팅 상태는 `GET /listings/{product_id}` 로 별도 조회.

---

## 5. 리스팅 — `/listings`

### `GET /listings/{product_id}` ✅ · 담당: 이여원(백B)
상품의 플랫폼별 등록 현황(소유권 검증, 미소유 `404`).

응답 `200` `ListingOut[]`
```json
[
  {
    "id": "uuid",
    "product_id": "uuid",
    "platform": "karrot",
    "platform_product_id": "string",
    "status": "active",
    "listed_at": "datetime"
  }
]
```

### `POST /listings/{listing_id}/sold` 🚧 · 담당: 작업 8
수동 판매완료 → 나머지 플랫폼 자동 삭제 트리거.

---

## 6. 플랫폼 계정 — `/platform-accounts` 🚧 · 담당: 이여원(백B)

> ⚠️ **합의 필요**: 이 라우트는 현재 `schemas/platform.py` 가 아닌 라우트 내부 인라인 모델을 사용한다.
> 응답 `id` 타입이 라우트(`str`)와 `schemas/platform.py`(`uuid`)에서 불일치 → 작업 1에서 통일.

### `GET /platform-accounts`
응답 `PlatformAccountOut[]`
```json
[ { "id": "string|uuid", "platform": "karrot", "is_active": true } ]
```

### `POST /platform-accounts`
요청 `PlatformAccountCreate`
```json
{ "platform": "karrot", "username": "string", "password": "string" }
```
> 자격증명은 Secrets Manager 에 저장하고 평문은 즉시 폐기. DB 엔 key ref 만 저장.

### `DELETE /platform-accounts/{account_id}`
응답 `204`.

---

## 7. 플랫폼 식별자

`platform` 필드 허용 값: `karrot`(당근) · `bunjang`(번개장터) · `fruits` · `charan`(차란) · `junggonara`(중고나라) · `ebay`(추후).

**현재 활성(웹 등록 가능) 플랫폼**: `bunjang`, `junggonara` 만. 당근·차란·fruits 는 앱 전용이라 비활성, eBay 는 추후 대상이다. `POST /products` 의 `platforms` 에 비활성 값이 오면 `422` 로 거절한다. (단일 출처: `app/domain/mapping/config.py` 의 `ACTIVE_PLATFORMS`)

---

## 8. 작업 1 합의 필요 항목 (요약)

1. **오류 응답 형식**: FastAPI 기본 `{"detail"}` vs steering 공통 `{"error_code", "message", "details"}`.
2. **platform-accounts 스키마 통일**: 인라인 모델 → `schemas/platform.py`, `id` 타입(`uuid`) 정합.
3. **analyze 응답 ↔ ProductCreate 매핑**: 표준_상품에 `colors: list[str]` / `materials: list[str]` 추가 완료. 단 `AIAnalysisResult.material` 은 아직 단일 `str` → 윤채린 쪽에서 `materials: list[str]` 로 맞추면 정합. 계절·패턴·스타일(차란)은 매핑 엔진 구현 시 추가 예정.
4. **목록 응답에 리스팅 상태 포함 여부**: 프론트 대시보드에서 상태 배지가 필요하면 `ProductOut` 에 요약 추가 검토.
