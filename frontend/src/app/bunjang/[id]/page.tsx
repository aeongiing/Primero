"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getProduct } from "@/lib/api";

interface Props {
  params: Promise<{ id: string }>;
}

const CONDITIONS: Record<number, string> = {
  10: "새상품", 9: "새상품", 8: "사용감 없음", 7: "사용감 없음",
  6: "사용감 적음", 5: "사용감 적음", 4: "사용감 많음", 3: "사용감 많음",
  2: "고장/파손 있음", 1: "고장/파손 있음",
};

export default function BunjangProductPage({ params }: Props) {
  const { id } = use(params);
  const router = useRouter();
  const [index, setIndex] = useState(0);
  const [liked, setLiked] = useState(false);
  const [product, setProduct] = useState<{
    title: string; price: number; description: string;
    condition: number; size: string | null; category: string;
    imageUrls: string[];
  } | null>(null);

  useEffect(() => {
    getProduct(id).then((p) => {
      const sorted = [...(p.images ?? [])].sort((a, b) => a.order - b.order);
      setProduct({
        title: p.title,
        price: p.price,
        description: p.description,
        condition: p.condition,
        size: p.size,
        category: p.category,
        imageUrls: sorted.map((img) => img.url),
      });
    }).catch(() => {});
  }, [id]);

  const imgs = product?.imageUrls ?? [];
  const count = imgs.length;

  return (
    <div className="min-h-screen bg-white">
      {/* 번개장터 네비게이션 바 */}
      <div className="sticky top-0 z-10 flex items-center border-b border-gray-200 bg-white px-4 py-3">
        <button onClick={() => router.back()} className="mr-3 text-gray-600 text-xl">←</button>
        <span className="text-base font-black text-[#F5511E]">⚡번개장터</span>
        <div className="ml-auto flex items-center gap-4 text-gray-500">
          <button aria-label="검색">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          </button>
          <button aria-label="공유">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.59 13.51 6.83 3.98M15.41 6.51 8.59 10.49"/></svg>
          </button>
          <button aria-label="더보기">⋯</button>
        </div>
      </div>

      {/* 이미지 캐러셀 */}
      <div className="relative aspect-square bg-gray-100">
        {imgs[index] ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={imgs[index]} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-gray-300 text-4xl">📷</div>
        )}
        {count > 1 && (
          <>
            <button onClick={() => setIndex((i) => (i - 1 + count) % count)}
              className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-white/80 p-2 shadow text-lg">‹</button>
            <button onClick={() => setIndex((i) => (i + 1) % count)}
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-white/80 p-2 shadow text-lg">›</button>
            <span className="absolute bottom-3 right-3 rounded-full bg-black/50 px-2.5 py-1 text-xs text-white font-medium">
              {index + 1}/{count}
            </span>
          </>
        )}
      </div>

      {/* 썸네일 */}
      {count > 1 && (
        <div className="flex gap-1.5 overflow-x-auto px-4 py-2 border-b border-gray-100">
          {imgs.map((url, i) => (
            <button key={i} onClick={() => setIndex(i)}
              className={`h-14 w-14 shrink-0 overflow-hidden rounded-lg border-2 transition-colors ${i === index ? "border-[#F5511E]" : "border-transparent"}`}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={url} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}

      {/* 판매자 정보 */}
      <div className="flex items-center gap-3 border-b border-gray-100 px-4 py-3">
        <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-400 text-lg">👤</div>
        <div>
          <p className="text-sm font-bold text-gray-900">이아오웅</p>
          <p className="text-xs text-green-500 font-medium">● 접속중</p>
        </div>
        <button className="ml-auto rounded-lg border border-gray-300 px-4 py-1.5 text-sm font-medium text-gray-700">
          프로필 보기
        </button>
      </div>

      {/* 상품 정보 */}
      <div className="px-4 py-4">
        <p className="text-lg font-bold text-gray-900 leading-snug">{product?.title ?? "로딩 중..."}</p>
        <div className="mt-1.5 flex items-center gap-2 text-xs text-gray-400">
          {product?.category && <span>{product.category}</span>}
          {product?.category && <span>·</span>}
          <span>방금 전</span>
        </div>
        <p className="mt-3 text-2xl font-black text-gray-900">
          {product ? product.price.toLocaleString("ko-KR") + "원" : ""}
        </p>

        {/* 상품 상태 */}
        {product && (
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600 font-medium">
              {CONDITIONS[Math.round(product.condition)] ?? "사용감 없음"}
            </span>
            {product.size && (
              <span className="rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600 font-medium">
                {product.size}
              </span>
            )}
          </div>
        )}

        {/* 설명 */}
        <p className="mt-4 whitespace-pre-line text-sm leading-relaxed text-gray-700">
          {product?.description}
        </p>
      </div>

      {/* 구분선 */}
      <div className="h-2 bg-gray-50" />

      {/* 관련 상품 */}
      <div className="px-4 py-4">
        <p className="text-sm font-bold text-gray-900 mb-3">판매자의 다른 상품</p>
        <p className="text-sm text-gray-400">등록된 다른 상품이 없어요</p>
      </div>

      {/* 하단 고정 바 */}
      <div className="fixed inset-x-0 bottom-0 flex items-center gap-3 border-t border-gray-200 bg-white px-4 py-3">
        <button
          onClick={() => setLiked((v) => !v)}
          className={`flex flex-col items-center gap-0.5 text-xs ${liked ? "text-[#F5511E]" : "text-gray-400"}`}
        >
          <span className="text-xl">{liked ? "♥" : "♡"}</span>
          <span>{liked ? "1" : "0"}</span>
        </button>
        <button className="flex-1 rounded-xl bg-[#F5511E] py-3 text-sm font-bold text-white shadow">
          구매하기
        </button>
      </div>
      <div className="h-20" />
    </div>
  );
}
