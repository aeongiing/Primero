"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getMe,
  listPlatformAccounts,
  disconnectPlatform,
  clearToken,
  getToken,
  type MeOut,
  type PlatformAccountOut,
} from "@/lib/api";

const PLATFORMS = [
  {
    key: "bunjang",
    label: "번개장터",
    color: "#FA2828",
    loginUrl: "https://bunjang.co.kr/login",
    available: true,
  },
  {
    key: "junggonara",
    label: "중고나라",
    color: "#2DB400",
    loginUrl: "https://web.joongna.com/login",
    available: true,
  },
  {
    key: "fruits",
    label: "Fruits",
    color: "#111111",
    loginUrl: null,
    available: false,
  },
  {
    key: "ebay",
    label: "eBay",
    color: "#0064D2",
    loginUrl: null,
    available: false,
  },
] as const;

export default function MyPage() {
  const router = useRouter();
  const [me, setMe] = useState<MeOut | null>(null);
  const [accounts, setAccounts] = useState<PlatformAccountOut[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    Promise.all([getMe(), listPlatformAccounts()])
      .then(([meData, accountsData]) => {
        setMe(meData);
        setAccounts(accountsData);
      })
      .catch(() => router.replace("/login"))
      .finally(() => setLoading(false));
  }, [router]);

  const connectedMap = Object.fromEntries(
    accounts.map((a) => [a.platform, a])
  );

  const handleDisconnect = async (accountId: string) => {
    await disconnectPlatform(accountId);
    setAccounts((prev) => prev.filter((a) => a.id !== accountId));
  };

  const handleLogout = () => {
    clearToken();
    router.push("/login");
  };

  if (loading) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-12">
        <p className="text-sm text-muted-foreground">불러오는 중…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      {/* 판매자 정보 */}
      <section className="rounded-xl border border-border bg-muted/30 p-6">
        <h1 className="text-lg font-bold">판매자 정보</h1>
        <div className="mt-4 flex flex-col gap-2 text-sm">
          <div className="flex items-center gap-3">
            <span className="w-20 text-muted-foreground">이메일</span>
            <span>{me?.email}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-20 text-muted-foreground">가입일</span>
            <span>
              {me?.created_at
                ? new Date(me.created_at).toLocaleDateString("ko-KR")
                : "-"}
            </span>
          </div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="mt-5 rounded-lg border border-border px-4 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted"
        >
          로그아웃
        </button>
      </section>

      {/* 플랫폼 계정 연결 */}
      <section className="mt-8">
        <h2 className="text-base font-bold">플랫폼 계정 연결</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          연결된 플랫폼에 상품이 자동으로 등록됩니다.
        </p>
        <ul className="mt-4 flex flex-col gap-3">
          {PLATFORMS.map((p) => {
            const connected = connectedMap[p.key];
            return (
              <li
                key={p.key}
                className="flex items-center justify-between rounded-xl border border-border bg-background px-5 py-4"
              >
                <div className="flex items-center gap-3">
                  <span
                    className="size-3 rounded-full"
                    style={{ background: p.color }}
                  />
                  <span className="text-sm font-medium">{p.label}</span>
                  {!p.available && (
                    <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
                      준비 중
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {connected ? (
                    <>
                      <span className="text-xs text-green-600">연결됨</span>
                      <button
                        type="button"
                        onClick={() => handleDisconnect(connected.id)}
                        className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-muted"
                      >
                        연결 해제
                      </button>
                    </>
                  ) : p.available ? (
                    <a
                      href={p.loginUrl!}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
                    >
                      계정 연결
                    </a>
                  ) : (
                    <span className="text-xs text-muted-foreground">-</span>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </section>
    </main>
  );
}
