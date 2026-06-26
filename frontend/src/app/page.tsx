"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { PLATFORMS, UPLOAD_PLATFORMS } from "@/lib/constants";
import type { Platform } from "@/types";
import { listProducts, type ProductOut } from "@/lib/api";

type Sale = "listed" | "sold" | "draft";

interface MyProduct {
  id: string;
  title: string;
  price: number;
  gender?: "우먼즈웨어" | "맨즈웨어";
  major: "아우터" | "상의" | "하의";
  sale: Sale;
  createdAt: string; // ISO
  listings: Partial<Record<Platform, "success" | "pending" | "failed">>;
}

// 백엔드 ProductOut → 홈 카드 모델
function mapProduct(p: ProductOut): MyProduct {
  const major = (["아우터", "상의", "하의"].find((m) => p.category?.includes(m)) ??
    "상의") as MyProduct["major"];
  const sale: Sale =
    p.status === "sold" ? "sold" : p.status === "draft" ? "draft" : "listed";
  return {
    id: p.id,
    title: p.title,
    price: p.price,
    major,
    sale,
    createdAt: (p.created_at ?? "").slice(0, 10),
    listings: {},
  };
}

// TODO(연동): GET /api/v1/products (내 상품). 현재는 레이아웃용 목 데이터.
const MOCK: MyProduct[] = [
  { id: "1", title: "준야와타나베 플란넬 M-65 필드 자켓", price: 585000, gender: "맨즈웨어", major: "아우터", sale: "listed", createdAt: "2026-06-20", listings: { bunjang: "success", joonggonara: "success", fruits: "success", ebay: "pending" } },
  { id: "2", title: "스톤아일랜드 니트 집업", price: 220000, gender: "맨즈웨어", major: "상의", sale: "listed", createdAt: "2026-06-18", listings: { bunjang: "success", fruits: "success" } },
  { id: "3", title: "마르지엘라 5포켓 데님", price: 175000, gender: "우먼즈웨어", major: "하의", sale: "sold", createdAt: "2026-06-10", listings: { bunjang: "success", joonggonara: "success", ebay: "success" } },
  { id: "4", title: "빈티지 체크 울 코트", price: 98000, gender: "우먼즈웨어", major: "아우터", sale: "listed", createdAt: "2026-06-24", listings: { fruits: "success", ebay: "failed" } },
  { id: "5", title: "리바이스 501 빅사이즈", price: 64000, gender: "맨즈웨어", major: "하의", sale: "draft", createdAt: "2026-06-25", listings: {} },
  { id: "6", title: "캐시미어 라운드 니트", price: 89000, gender: "우먼즈웨어", major: "상의", sale: "listed", createdAt: "2026-06-15", listings: { bunjang: "success", joonggonara: "pending" } },
];

const SALE_TABS: { key: Sale | "all"; label: string }[] = [
  { key: "all", label: "전체 상품" },
  { key: "listed", label: "판매중" },
  { key: "sold", label: "판매완료" },
  { key: "draft", label: "임시저장" },
];

const SORTS = [
  { key: "recent", label: "최근 등록순" },
  { key: "old", label: "오래된 등록순" },
  { key: "price_high", label: "가격 높은순" },
  { key: "price_low", label: "가격 낮은순" },
] as const;

const CATEGORY_FILTERS = ["전체", "우먼즈웨어", "맨즈웨어", "아우터", "상의", "하의"];

const SALE_BADGE: Record<Sale, { label: string; cls: string }> = {
  listed: { label: "판매중", cls: "bg-brand text-brand-foreground" },
  sold: { label: "판매완료", cls: "bg-foreground/80 text-background" },
  draft: { label: "임시저장", cls: "bg-muted text-muted-foreground" },
};

export default function HomePage() {
  const [cat, setCat] = useState("전체");
  const [tab, setTab] = useState<Sale | "all">("all");
  const [sort, setSort] = useState<(typeof SORTS)[number]["key"]>("recent");
  const [items, setItems] = useState<MyProduct[]>(MOCK);

  // 실데이터 로드 — 인증/백엔드 미가용 시 목업 유지
  useEffect(() => {
    let alive = true;
    listProducts()
      .then((rows) => {
        if (alive && Array.isArray(rows)) setItems(rows.map(mapProduct));
      })
      .catch(() => {
        /* 미인증(401)·오프라인 → 목업 유지 */
      });
    return () => {
      alive = false;
    };
  }, []);

  const products = useMemo(() => {
    let list = items.filter((p) => {
      if (tab !== "all" && p.sale !== tab) return false;
      if (cat === "전체") return true;
      if (cat === "우먼즈웨어" || cat === "맨즈웨어") return p.gender === cat;
      return p.major === cat;
    });
    list = [...list].sort((a, b) => {
      if (sort === "recent") return b.createdAt.localeCompare(a.createdAt);
      if (sort === "old") return a.createdAt.localeCompare(b.createdAt);
      if (sort === "price_high") return b.price - a.price;
      return a.price - b.price;
    });
    return list;
  }, [cat, tab, sort, items]);

  return (
    <main className="mx-auto max-w-[1280px] px-6 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">상품 관리</h1>
        <Link
          href="/upload"
          className="rounded-lg bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground transition-colors hover:bg-primary/90"
        >
          + 상품 등록
        </Link>
      </div>

      <div className="mt-6 flex gap-8">
        {/* 좌측 카테고리 필터 */}
        <aside className="w-44 shrink-0">
          <h2 className="px-2 text-xs font-bold text-muted-foreground">카테고리</h2>
          <ul className="mt-2 flex flex-col">
            {CATEGORY_FILTERS.map((c) => (
              <li key={c}>
                <button
                  type="button"
                  onClick={() => setCat(c)}
                  className={`w-full rounded-md px-2 py-2 text-left text-sm transition-colors ${
                    cat === c ? "bg-accent font-bold text-accent-foreground" : "hover:bg-muted"
                  }`}
                >
                  {c}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        {/* 우측 본문 */}
        <section className="flex-1">
          {/* 상태 탭 + 정렬 */}
          <div className="flex items-center justify-between border-b">
            <div className="flex gap-1">
              {SALE_TABS.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  onClick={() => setTab(t.key)}
                  className={`-mb-px border-b-2 px-3 py-2.5 text-sm transition-colors ${
                    tab === t.key
                      ? "border-primary font-bold text-foreground"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as (typeof SORTS)[number]["key"])}
              aria-label="정렬"
              className="h-9 rounded-md border border-input bg-background px-2 text-sm outline-none focus:ring-2 focus:ring-ring"
            >
              {SORTS.map((s) => (
                <option key={s.key} value={s.key}>{s.label}</option>
              ))}
            </select>
          </div>

          <p className="mt-4 text-sm text-muted-foreground">총 {products.length}개</p>

          {products.length === 0 ? (
            <div className="mt-16 text-center text-sm text-muted-foreground">
              조건에 맞는 상품이 없어요.
            </div>
          ) : (
            <div className="mt-4 grid grid-cols-2 gap-5 sm:grid-cols-3">
              {products.map((p) => (
                <Link key={p.id} href={`/products/${p.id}`} className="group">
                  <div className="relative aspect-square overflow-hidden rounded-lg bg-muted">
                    <span
                      className={`absolute left-2 top-2 rounded px-2 py-0.5 text-xs font-bold ${SALE_BADGE[p.sale].cls}`}
                    >
                      {SALE_BADGE[p.sale].label}
                    </span>
                  </div>
                  <p className="mt-2 truncate text-sm font-medium group-hover:text-brand">{p.title}</p>
                  <p className="text-base font-bold">{p.price.toLocaleString("ko-KR")}원</p>
                  {/* 플랫폼별 등록 현황 */}
                  <div className="mt-1.5 flex items-center gap-1.5">
                    {UPLOAD_PLATFORMS.map((plat) => {
                      const st = p.listings[plat];
                      return (
                        <span
                          key={plat}
                          title={`${PLATFORMS[plat].label}: ${st ?? "미등록"}`}
                          className="size-2.5 rounded-full"
                          style={{
                            background: st === "success" ? PLATFORMS[plat].color : "transparent",
                            border: st === "success" ? "none" : "1.5px solid var(--border)",
                            opacity: st === "pending" ? 0.5 : 1,
                          }}
                        />
                      );
                    })}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
