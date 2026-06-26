"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getToken, clearToken } from "@/lib/api";

function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

export default function SiteHeader() {
  const pathname = usePathname();
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(!!getToken());
  }, [pathname]);

  const handleLogout = () => {
    clearToken();
    setLoggedIn(false);
    window.location.href = "/login";
  };

  return (
    <header className="border-b">
      {/* 상단 다크 프로모 바 */}
      <div className="bg-foreground text-background">
        <div className="mx-auto flex h-11 max-w-[1280px] items-center justify-center gap-4 px-6 text-[15px]">
          <span className="text-lg font-bold" style={{ fontFamily: "var(--font-logo)" }}>ParaPara</span>
          <span className="text-background/90">한 번 등록하면 여러 플랫폼에 자동 등록돼요</span>
          <Link
            href="/upload"
            className="rounded-full bg-brand px-3.5 py-1.5 text-sm font-semibold text-brand-foreground"
          >
            지금 바로 등록해보기
          </Link>
        </div>
      </div>

      {/* 메인 헤더 */}
      <div>
        <div className="mx-auto flex h-16 max-w-[1280px] items-center gap-7 px-6">
          <Link
            href="/"
            className="text-3xl font-bold text-brand"
            style={{ fontFamily: "var(--font-logo)" }}
          >
            ParaPara
          </Link>

          <label className="relative flex flex-1 items-center">
            <span className="absolute left-4 text-muted-foreground">
              <SearchIcon />
            </span>
            <input
              type="search"
              placeholder="내 상품 검색"
              aria-label="내 상품 검색"
              className="h-12 w-full rounded-full bg-muted pl-12 pr-4 text-[15px] outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring"
            />
          </label>

          <nav className="flex items-center gap-6 text-[15px]">
            {loggedIn ? (
              <>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="hover:text-brand transition-colors"
                >
                  로그아웃
                </button>
                <Link href="/mypage" className="hover:text-brand transition-colors">
                  마이페이지
                </Link>
              </>
            ) : (
              <Link href="/login" className="hover:text-brand transition-colors">
                로그인
              </Link>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
