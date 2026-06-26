import type { Platform } from "@/types";

export const PLATFORMS: Record<Platform, { label: string; color: string }> = {
  karrot: { label: "당근마켓", color: "#FF6F0F" },
  bunjang: { label: "번개장터", color: "#F03C00" },
  fruits: { label: "Fruits", color: "#4CAF50" },
  charan: { label: "차란", color: "#6366F1" },
  ebay: { label: "eBay", color: "#E53238" },
};

// 사진 순서 기준 (기획서 명세)
export const IMAGE_ORDER_LABELS = [
  "앞면",
  "확대",
  "뒷면",
  "디테일",
  "오염",
  "태그",
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
