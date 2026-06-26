"use client";

import { useState } from "react";
import Link from "next/link";

// TODO(연동): 백엔드 GET /api/v1/products/{id} 로 교체. 현재는 레이아웃용 목 데이터.
const MOCK = {
  brand: "Junya Watanabe",
  title: "06FW 준야와타나베 플란넬 M-65 필드 자켓 (on.767)",
  price: 585000,
  condition: 8,
  size: "S",
  chest: 54,
  total_length: 78,
  description:
    "06FW Junya Watanabe 꼼데가르송 라인 M-65 필드자켓입니다. 다른 플랫폼 또한 유일매물이며 클래식한 밀리터리 무드에 준야 와타나베 특유의 감성이 한스푼 더해진 제품입니다. 사진보다 실물이 훨씬 멋스러운 자켓이며 자연스러운 핏감과 디테일이 돋보여 아카이브를 좋아하시는 분들에게 추천드립니다.",
  category: ["맨즈웨어", "아우터"],
  listedAgo: "1개월 전",
  seller: { name: "Eastate" },
  images: 4,
};

function Money({ value }: { value: number }) {
  return <span>₩ {value.toLocaleString("ko-KR")}</span>;
}

export default function ProductDetailPage() {
  const [index, setIndex] = useState(0);

  const prev = () => setIndex((i) => (i - 1 + MOCK.images) % MOCK.images);
  const next = () => setIndex((i) => (i + 1) % MOCK.images);

  return (
    <main className="mx-auto max-w-[1280px] px-6 py-8">
      <div className="grid gap-8 lg:grid-cols-2">
        {/* 좌: 이미지 캐러셀 */}
        <div>
          <div className="relative aspect-square overflow-hidden rounded-lg bg-muted">
            <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
              이미지 {index + 1} / {MOCK.images}
            </div>
            <button
              type="button"
              onClick={prev}
              aria-label="이전 사진"
              className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-white/90 p-2 shadow-sm transition-colors hover:bg-white"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="m15 18-6-6 6-6" />
              </svg>
            </button>
            <button
              type="button"
              onClick={next}
              aria-label="다음 사진"
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-white/90 p-2 shadow-sm transition-colors hover:bg-white"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="m9 18 6-6-6-6" />
              </svg>
            </button>
          </div>
          {/* 썸네일 dot */}
          <div className="mt-3 flex justify-center gap-1.5">
            {Array.from({ length: MOCK.images }).map((_, i) => (
              <button
                key={i}
                type="button"
                aria-label={`${i + 1}번 사진 보기`}
                onClick={() => setIndex(i)}
                className={`h-2 w-2 rounded-full transition-colors ${
                  i === index ? "bg-primary" : "bg-border"
                }`}
              />
            ))}
          </div>
        </div>

        {/* 우: 정보 */}
        <div className="flex flex-col gap-4">
          <div className="flex items-start justify-between gap-4">
            <Link href="#" className="text-base font-bold text-foreground underline underline-offset-2 hover:text-brand">
              {MOCK.brand}
            </Link>
            <button type="button" aria-label="공유" className="text-muted-foreground hover:text-foreground">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="18" cy="5" r="3" />
                <circle cx="6" cy="12" r="3" />
                <circle cx="18" cy="19" r="3" />
                <path d="m8.59 13.51 6.83 3.98M15.41 6.51 8.59 10.49" />
              </svg>
            </button>
          </div>

          <h1 className="text-xl font-bold leading-snug">{MOCK.title}</h1>

          <p className="text-2xl font-bold"><Money value={MOCK.price} /></p>

          <dl className="grid grid-cols-[5rem_1fr] gap-y-2 text-sm">
            <dt className="text-muted-foreground">컨디션</dt>
            <dd>{MOCK.condition}/10 (상태 좋음)</dd>
            <dt className="text-muted-foreground">사이즈</dt>
            <dd>{MOCK.size} · 가슴단면 {MOCK.chest}cm · 총장 {MOCK.total_length}cm</dd>
          </dl>

          <p className="whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
            {MOCK.description}
          </p>

          <div className="flex items-center gap-2 text-sm">
            {MOCK.category.map((c) => (
              <span key={c} className="rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">
                {c}
              </span>
            ))}
            <span className="ml-auto text-muted-foreground">{MOCK.listedAgo}</span>
          </div>

          {/* 안전결제 안내 */}
          <div className="flex items-center gap-2 rounded-lg bg-accent px-4 py-3 text-sm">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <path d="m9 11 3 3L22 4" />
            </svg>
            <span>한 번 등록으로 <strong className="font-semibold">여러 플랫폼에 자동 등록·동기화</strong>돼요</span>
          </div>

          {/* 판매자 정보 */}
          <div className="mt-2">
            <h2 className="text-lg font-bold">판매자 정보</h2>
            <div className="mt-3 flex items-center gap-3 rounded-lg border p-3">
              <div className="h-11 w-11 shrink-0 rounded-full bg-muted" />
              <p className="text-sm font-medium">{MOCK.seller.name}</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
