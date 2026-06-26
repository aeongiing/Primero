# Primero — 프론트엔드 디자인 시스템

> fruits(fruitsfamily.com)의 **구성·폰트·레이아웃을 그대로 차용**하되, **컬러만 Primero 브랜드 팔레트**로 교체한다.
> 인증은 **Google 로그인 단일** 지원(Facebook·Kakao 미지원).
> 스택: Next.js(App Router) · React · TS · Tailwind v4 · shadcn 토큰 · base-ui.

---

## 1. 디자인 원칙 (fruits 차용)

- **클린 화이트 베이스 + 고대비 잉크 텍스트.** 장식 최소화, 여백으로 위계 표현.
- **콘텐츠 중앙 정렬, 넓은 좌우 여백.** 본문 컨테이너 `max-w-[1024px]`.
- **둥근 풀(pill) 검색바**가 헤더 중앙을 차지하는 마켓형 상단 구조.
- **상세 페이지는 2단**: 좌측 이미지 캐러셀(정사각), 우측 정보 컬럼.
- 인터랙션은 절제 — hover 시 미세한 배경/색 변화, 굵은 그림자 지양.

## 2. 컬러 팔레트 (Primero)

**메인 컬러: Pantone 17-1230 Mocha Mousse** (2025 올해의 컬러, `#A47864`). 빈티지·중고 의류의 따뜻함과 차분한 프리미엄 무드를 담은 브라운. fruits식 흑/백 미니멀 위에 모카 브라운을 CTA·포인트로 얹는다. 버튼·로고·링크·포커스에 `#A47864`를 그대로 사용한다.

| 역할 | 토큰 | HEX | 용도 |
|---|---|---|---|
| Primary / Brand (Mocha Mousse) | `--primary` · `--brand` | `#A47864` | 버튼·회원가입·로고·링크·안전결제·포커스링 |
| Primary fg | `--primary-foreground` | `#FDFBF9` | 모카 버튼 위 텍스트 |
| Accent (연한 모카 크림) | `--accent` | `#F3ECE6` | 안전결제 배너·칩 배경 |
| Accent fg / 보조 강조 텍스트 | `--accent-foreground` | `#6B4A38` | 연한 배경 위 진한 모카 텍스트 |
| Ink (본문) | `--foreground` | `#1E1A17` | 제목·본문, 프로모바 배경 |
| Background | `--background` | `#FFFFFF` | 페이지 |
| Muted bg | `--muted` | `#F6F4F2` | 검색바·입력 배경 |
| Muted fg | `--muted-foreground` | `#77716B` | 보조 텍스트, placeholder |
| Border | `--border` / `--input` | `#E7E4E1` | 경계선, 입력 테두리 |
| Ring (focus) | `--ring` | `#A47864` | 포커스 링 |
| Destructive | `--destructive` | `#DC2626` | 삭제·오류 |

> 참고: `#A47864` 위 흰 텍스트 대비는 약 3.8:1로 일반 텍스트 AA(4.5:1)에는 살짝 못 미친다. 버튼 텍스트는 굵게(`font-semibold`)·큰 사이즈로 써서 대형 텍스트 기준(3:1)을 만족시키고, 본문용 진한 텍스트는 `--accent-foreground`(`#6B4A38`)를 쓴다.

**색 사용 원칙**: 화면의 대부분은 흰 배경 + 잉크 텍스트. 모카 브라운은 "누르는 곳 / 안전 / 활성"에만 절제해서 써서 따뜻하고 프리미엄한 인상을 준다.

**플랫폼 배지 색**(상품-플랫폼 연결 표시용, `lib/constants.ts`와 일치):
당근 `#FF6F0F` · 번개장터 `#F03C00` · Fruits `#4CAF50` · 차란 `#6366F1` · eBay `#E53238`.
→ 이 색들은 **외부 플랫폼 식별용**으로만 쓰고, Primero UI 자체 색과 혼동하지 않는다.

## 3. 타이포그래피

- **본문 폰트: Pretendard** (한글·라틴 모두 커버). fruits와 동일 계열의 한국형 산세리프.
  - 폴백: `Pretendard, -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif`
  - 기존 Geist(라틴 전용)는 한글 미지원이라 교체.
- 스케일

| 용도 | class | size / line | weight |
|---|---|---|---|
| 페이지 타이틀(로그인 "로그인" 등) | `text-2xl` | 24 / 1.3 | 700 |
| 상품명 | `text-xl` | 20 / 1.4 | 700 |
| 섹션 헤딩 | `text-lg` | 18 / 1.4 | 600 |
| 본문 | `text-sm` | 14 / 1.6 | 400 |
| 보조/메타 | `text-xs` | 12 / 1.5 | 400, `text-muted-foreground` |
| 가격 강조 | `text-lg font-bold` | 18 | 700 |

## 4. 레이아웃 & 스페이싱

- 컨테이너: `mx-auto max-w-[1024px] px-4`.
- 수직 리듬: 섹션 간 `gap-6`~`gap-10`, 폼 필드 간 `gap-4`.
- 라운드: 입력/카드 `rounded-lg`(≈10px), 검색바·소셜버튼 `rounded-full`, 버튼 `rounded-lg`.
- 보더: 헤더 하단·카드 `border` + `--border`.
- 그림자: 기본 무그림자, 떠 있는 요소만 `shadow-sm`.

## 5. 핵심 컴포넌트

### Header (`layout.tsx`)
fruits 구조 차용:
1. (선택) 상단 다크 프로모 바 — 추후. MVP에선 생략 가능.
2. 메인 헤더: 좌측 **로고(Primero)** · 중앙 **풀형 검색바** · 우측 **마켓/판매/로그인** + `회원 가입`(브랜드 채움 버튼).
3. 하단 **카테고리 nav row**: 맨즈웨어/우먼즈웨어/… (드롭다운). MVP에선 단순 링크로 시작.

### Button (이미 `components/ui/button.tsx` 존재)
- `default` = 브랜드 바이올렛 채움(`bg-primary`), hover 시 `--primary` 5% 어둡게.
- `outline` = 흰 배경 + 보더(로그인 등).
- `ghost`/`secondary`/`link` 기존 유지.
- 소셜 로그인 버튼은 별도 풀형 변형으로 구성(아래 6번).

### Form Field
- 라벨(`text-sm font-medium`) → 입력(`h-11 rounded-lg border px-3 text-sm`, focus `ring-2 ring-ring`).
- 에러: 필드 하단 `text-xs text-destructive`.

### Card
- `rounded-lg border bg-card p-4`. 판매자 정보·요약 카드에 사용.

### Badge / Chip
- 카테고리·상태 칩: `rounded-full bg-accent text-primary text-xs px-2.5 py-1`.

## 6. 페이지 블루프린트

### 6-1. 로그인 (`/login`) — **Google 단일**
fruits 로그인 레이아웃을 차용하되, 이메일/비번 폼과 Facebook/Kakao는 **제거**하고 Google 버튼만 중앙 배치.
```
[중앙 카드, max-w-[400px]]
  Primero 로고
  h1 "로그인"                      (text-2xl font-bold, 중앙)
  p  "Google 계정으로 시작하세요"   (text-sm text-muted-foreground)
  ─────────────────────────────
  [ G  Google로 계속하기 ]          (rounded-full, 흰 배경 + 보더, 구글 로고)
  ─────────────────────────────
  p  약관/개인정보 안내 (text-xs text-muted-foreground)
```
- Google 버튼: `w-full h-12 rounded-full border bg-white text-sm font-medium`, 좌측 구글 G 아이콘, hover `bg-muted`.
- 클릭 시 백엔드 Google OAuth(`/api/v1/auth/google`)로 리다이렉트(연동은 백엔드B 담당, 프론트는 진입점만).

### 6-2. 상품 상세 (`/products/[id]`) — fruits 2단 차용
```
[max-w-[1024px], 좌우 2단 (lg:grid-cols-2)]
 좌: 이미지 캐러셀 (정사각 aspect-square, 좌우 화살표, 썸네일 dot)
 우:
   브랜드명 (text-primary font-bold, 링크 스타일)   [♡찜수] [공유]
   상품명 (text-xl font-bold)
   설명 블록 (text-sm, 줄바꿈 보존)
     - Price : ₩ 000
     - Condition : n/10
     - Size : ...
   카테고리 브레드크럼 (남자 > 아우터 > 자켓)  · 등록 경과(1개월 전)
   [안전결제 안내 배너] (rounded-lg bg-accent, success 체크 아이콘)
   ── 판매자 정보 ──
   [아바타] 닉네임 / N 팔로워            [팔로우 버튼(outline)]
```
- 색만 Primero로: 브랜드명/링크/활성요소 = `--primary`, 안내 배너 체크 = success.
- **타 플랫폼 연결 영역은 이번 범위 제외**(추후).

## 7. 디렉터리 규칙

```
src/
├── app/
│   ├── login/page.tsx          ← 신규(Google 단일)
│   ├── products/[id]/page.tsx  ← 상세(2단)
│   └── ...
├── components/
│   ├── ui/        ← 프리미티브(button 등 shadcn/base-ui)
│   └── layout/    ← Header, Footer, SearchBar 등 공용
└── lib/, types/, store/, hooks/
```
- 공용 레이아웃 컴포넌트(Header/SearchBar/CategoryNav)는 `components/layout/`에 분리.
- 페이지는 조립만, 로직은 hooks/store로.

## 8. 접근성

- 색 대비 WCAG AA: 본문 ≥ 4.5:1, 큰 텍스트 ≥ 3:1. (바이올렛 `#5B3FB8` 위 흰 텍스트 대비 충족.)
- 모든 인터랙티브 요소 키보드 포커스 + 가시 포커스링(`--ring`).
- 이미지 `alt`, 아이콘 버튼 `aria-label` 필수.
- 폼 라벨-입력 `htmlFor`/`id` 연결.

> 전체 WCAG 준수 확정은 보조기술 수동 테스트 + 전문가 검토가 별도로 필요하다.
