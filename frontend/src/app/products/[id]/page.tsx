"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { getProduct, type ProductOut } from "@/lib/api";

interface Props {
  params: Promise<{ id: string }>;
}

interface DetailData {
  brand: string;
  title: string;
  price: number;
  condition: number;
  size: string | null;
  chest: number | null;
  total_length: number | null;
  description: string;
  category: string[];
  listedAgo: string;
  seller: { name: string };
  imageUrls: string[];
}

// 기본 목업 (백엔드 미가용/미인증 시 표시)
const MOCK: DetailData = {
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
  imageUrls: [
    "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800&h=800&fit=crop&crop=center",
    "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=800&h=800&fit=crop&crop=center",
    "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=800&h=800&fit=crop&crop=center",
    "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800&h=800&fit=crop&crop=center",
  ],
};

function relTime(iso: string): string {
  if (!iso) return "";
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  if (days <= 0) return "오늘";
  if (days < 30) return `${days}일 전`;
  return `${Math.floor(days / 30)}개월 전`;
}

function fromProduct(p: ProductOut, id: string): DetailData {
  const sorted = [...(p.images ?? [])].sort((a, b) => a.order - b.order);
  return {
    brand: p.brand || "",
    title: p.title,
    price: p.price,
    condition: p.condition,
    size: p.size,
    chest: p.chest,
    total_length: p.total_length,
    description: p.description,
    category: p.category
      ? p.category.split(">").map((s) => s.trim()).filter(Boolean)
      : [],
    listedAgo: relTime(p.created_at),
    seller: { name: "판매자" },
    imageUrls: sorted.length > 0 ? sorted.map((img) => img.url) : (MOCK_IMAGES[id] ?? MOCK.imageUrls),
  };
}

// 홈 목업과 동일한 썸네일 (ID → URL 매핑)
const MOCK_IMAGES: Record<string, string[]> = {
  "1": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSINObEa_slTmm57AdENIOVcwxGwZG-OnFhNcQNUJY4vw&s"],
  "2": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRlmezO-s1jjel_7hvE_qUOYqgooGiEjHeYss_6BZ2ong&s=10"],
  "3": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSGJxh8NostVLbIsObRbKuP4IoVS2T4TVcMxug4Ubhe2g&s=10"],
  "4": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTz-BJ7GCGSw_sePkHVLjXaPsLrQ65CisAyrSEqS9pLCA&s=10"],
  "5": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTVhmpKFbjpDDK3SVIH9OcE4pBYMkNw_p9Ij0qkdjWMNw&s"],
  "6": ["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR27-Sc4F5Wh31vLEKUiOOajhh_DflAQeG1a9bPwsbyrw&s"],
};

function Money({ value }: { value: number }) {
  return <span>₩ {value.toLocaleString("ko-KR")}</span>;
}

export default function ProductDetailPage({ params }: Props) {
  const { id } = use(params);
  const [index, setIndex] = useState(0);
  const [data, setData] = useState<DetailData>({ ...MOCK, imageUrls: MOCK_IMAGES[id] ?? MOCK.imageUrls });

  // 실데이터 로드 — 미인증/오프라인 시 목업 유지
  useEffect(() => {
    let alive = true;
    getProduct(id)
      .then((p) => {
        if (alive) {
          setData(fromProduct(p, id));
          setIndex(0);
        }
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [id]);

  const count = data.imageUrls.length;
  const prev = () => setIndex((i) => (i - 1 + count) % count);
  const next = () => setIndex((i) => (i + 1) % count);

  const sizeLine = [
    data.size,
    data.chest != null ? `가슴단면 ${data.chest}cm` : null,
    data.total_length != null ? `총장 ${data.total_length}cm` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <main className="mx-auto max-w-[1280px] px-6 py-8">
      <div className="grid gap-8 lg:grid-cols-2">
        {/* 좌: 이미지 캐러셀 */}
        <div>
          <div className="relative aspect-square overflow-hidden rounded-lg bg-muted">
            {data.imageUrls[index] ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={data.imageUrls[index]}
                alt={`${data.title} ${index + 1}`}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
                이미지 {index + 1} / {count}
              </div>
            )}
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
          <div className="mt-3 flex justify-center gap-1.5">
            {data.imageUrls.map((_, i) => (
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
              {data.brand || "브랜드 미상"}
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

          <h1 className="text-xl font-bold leading-snug">{data.title}</h1>

          <p className="text-2xl font-bold"><Money value={data.price} /></p>

          <dl className="grid grid-cols-[5rem_1fr] gap-y-2 text-sm">
            <dt className="text-muted-foreground">컨디션</dt>
            <dd>{data.condition}/10</dd>
            <dt className="text-muted-foreground">사이즈</dt>
            <dd>{sizeLine || "-"}</dd>
          </dl>

          <p className="whitespace-pre-line text-sm leading-relaxed text-muted-foreground">
            {data.description}
          </p>

          <div className="flex items-center gap-2 text-sm">
            {data.category.map((c) => (
              <span key={c} className="rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">
                {c}
              </span>
            ))}
            {data.listedAgo && (
              <span className="ml-auto text-muted-foreground">{data.listedAgo}</span>
            )}
          </div>

          {/* 멀티플랫폼 안내 */}
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
              <p className="text-sm font-medium">{data.seller.name}</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
