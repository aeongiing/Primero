import type { Platform } from "@/types";

export const PLATFORMS: Record<Platform, { label: string; color: string }> = {
  // 1차 지원 (웹) — 각 플랫폼 대표색
  bunjang: { label: "번개장터", color: "#FA2828" },   // 번개 레드
  joonggonara: { label: "중고나라", color: "#2DB400" }, // 중고나라 그린
  fruits: { label: "Fruits", color: "#111111" },       // fruits 블랙(모노톤)
  ebay: { label: "eBay", color: "#0064D2" },           // eBay 블루
  // 2차 지원 (모바일 단계)
  charan: { label: "차란", color: "#6366F1" },
  karrot: { label: "당근마켓", color: "#FF6F0F" },
};

// 사진 순서 기준 (기획서 명세)
export const IMAGE_ORDER_LABELS = [
  "앞면",
  "뒷면",
  "태그",
  "디테일",
  "오염",
  "기타",
];

export const CATEGORIES = [
  "상의",
  "하의",
  "아우터",
  "원피스",
  "신발",
  "가방",
  "기타",
] as const;

export const SIZES = ["Free", "XS", "S", "M", "L", "XL", "XXL"] as const;

export const CONDITION_LABELS: Record<number, string> = {
  10: "새 상품",
  9: "거의 새 것",
  8: "상태 좋음",
  7: "사용감 적음",
  6: "사용감 있음",
  5: "보통",
  4: "하자 있음",
  3: "수선 필요",
  2: "부품용",
  1: "폐기 직전",
};

// ─────────────────────────────────────────────────────────────
// 표준_상품 정규 옵션 값 (플랫폼 input 명세 기준, 차란 = 최대 표현력)
// ─────────────────────────────────────────────────────────────

// 컨디션 등급 (차란 기준) — 점수(0~10)와 함께 보조 표시
export const CONDITION_GRADES = [
  { grade: "Excellent", desc: "택 포함 / 새 상품급", min: 9.0 },
  { grade: "Great", desc: "사용감 거의 없음", min: 8.0 },
  { grade: "Very-good", desc: "약간의 사용감", min: 6.5 },
  { grade: "Good", desc: "사용감 있음", min: 0 },
] as const;

// 핏감
export const FITS = ["정사이즈예요", "작은 편이에요", "큰 편이에요"] as const;

// 대표 색상 (차란 20색)
export const COLORS = [
  "블랙", "차콜", "그레이", "화이트", "아이보리", "베이지", "브라운",
  "카키", "그린", "민트", "네이비", "블루", "스카이 블루", "퍼플",
  "라벤더", "와인", "레드", "핑크", "오렌지", "옐로우",
] as const;

// 계절 (최대 4)
export const SEASONS = ["봄", "여름", "가을", "겨울"] as const;
export const SEASONS_MAX = 4;

// 패턴
export const PATTERNS = [
  "무지", "그래픽", "레터링", "스트라이프", "체크", "도트",
  "플라워", "페이즐리", "지브라", "레오파드", "타이다이",
] as const;

// 소재 (최대 4)
export const MATERIALS = [
  "면", "폴리에스터", "폴리우레탄", "스판덱스", "데님", "리넨", "울",
  "천연가죽", "인조가죽", "천연퍼", "인조퍼", "캐시미어", "앙고라",
  "알파카", "코듀로이", "나일론", "실크", "레이온", "모달", "기모",
  "모헤어", "엘라스틴", "아크릴", "덕다운", "구스다운", "스웨이드",
] as const;
export const MATERIALS_MAX = 4;

// 스타일
export const STYLES = [
  "스포티", "스트릿", "베이직", "러블리", "오피스", "캠퍼스", "청순", "섹시",
] as const;

// 성별 루트
export const GENDERS = ["여성의류", "남성의류"] as const;

// 카테고리 트리: 성별 > 대분류 > 중분류 (차란 기준)
export const CATEGORY_TREE: Record<string, Record<string, string[]>> = {
  여성의류: {
    아우터: ["재킷", "점퍼", "조끼", "집업", "코트", "카디건"],
    상의: ["니트", "티셔츠", "블라우스/셔츠"],
    하의: ["팬츠", "스커트"],
    원피스: ["원피스"],
    세트: ["기타세트", "정장세트", "트레이닝 세트"],
    비치웨어: ["상의", "상의세트", "스커트", "원피스", "팬츠"],
    수영복: ["모노키니", "반신수영복", "비키니", "원피스수영복", "전신수영복"],
  },
  남성의류: {
    아우터: ["재킷", "점퍼", "조끼", "집업", "코트", "카디건"],
    상의: ["니트", "티셔츠", "블라우스/셔츠"],
    하의: ["팬츠"],
    세트: ["정장세트", "트레이닝 세트", "기타세트"],
    비치웨어: ["상하세트", "상의", "세트"],
    수영복: ["남성사각팬츠", "남성삼각팬츠", "반신수영복", "전신수영복", "상의"],
  },
};

// 라벨 사이즈
export const LABEL_SIZES = ["S", "M", "L"] as const;

// 업로드 대상 플랫폼 — 1차(웹): 번개·중고나라·fruits·eBay. 차란·당근은 모바일 단계.
export const UPLOAD_PLATFORMS: Platform[] = ["bunjang", "joonggonara"];
export const LATER_PLATFORMS: Platform[] = ["charan", "karrot"];
