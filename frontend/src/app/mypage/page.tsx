"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  clearToken,
  getToken,
  getMe,
  type MeOut,
  listPlatformAccounts,
  disconnectPlatform,
  connectViaKakao,
  type PlatformAccountOut,
} from "@/lib/api";

const PLATFORMS = [
  { key: "bunjang",     label: "번개장터", color: "#FA2828", kakaoLogin: true },
  { key: "joonggonara", label: "중고나라", color: "#2DB400", kakaoLogin: false },
  { key: "fruits",      label: "Fruits",  color: "#111111", kakaoLogin: false },
  { key: "ebay",        label: "eBay",    color: "#0064D2", kakaoLogin: false },
] as const;

type PlatformKey = (typeof PLATFORMS)[number]["key"];

interface LoginForm {
  email: string;
  password: string;
  loading: boolean;
  error: string;
}

export default function MyPage() {
  const router = useRouter();
  const [me, setMe] = useState<MeOut | null>(null);
  const [accounts, setAccounts] = useState<PlatformAccountOut[]>([]);
  const [openForm, setOpenForm] = useState<PlatformKey | null>(null);
  const [forms, setForms] = useState<Record<string, LoginForm>>({});
  const [disconnecting, setDisconnecting] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) return;
    getMe().then(setMe).catch(() => {});
    listPlatformAccounts().then(setAccounts).catch(() => {});
  }, []);

  const handleLogout = () => {
    clearToken();
    router.push("/login");
  };

  const getForm = (key: string): LoginForm =>
    forms[key] ?? { email: "", password: "", loading: false, error: "" };

  const setForm = (key: string, patch: Partial<LoginForm>) =>
    setForms((prev) => ({ ...prev, [key]: { ...getForm(key), ...patch } }));

  const handleConnect = async (platformKey: PlatformKey) => {
    const form = getForm(platformKey);
    if (!form.email || !form.password) {
      setForm(platformKey, { error: "이메일과 비밀번호를 입력해주세요" });
      return;
    }
    setForm(platformKey, { loading: true, error: "" });
    try {
      const account = await connectViaKakao(platformKey, form.email, form.password);
      setAccounts((prev) => {
        const filtered = prev.filter((a) => a.platform !== platformKey);
        return [...filtered, account];
      });
      setOpenForm(null);
      setForm(platformKey, { email: "", password: "", loading: false, error: "" });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "연결 실패";
      setForm(platformKey, { loading: false, error: msg });
    }
  };

  const handleDisconnect = async (accountId: string) => {
    setDisconnecting(accountId);
    try {
      await disconnectPlatform(accountId);
      setAccounts((prev) => prev.filter((a) => a.id !== accountId));
    } finally {
      setDisconnecting(null);
    }
  };

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      {/* 판매자 정보 */}
      <section className="rounded-xl border border-border bg-muted/30 p-6">
        <h1 className="text-lg font-bold">판매자 정보</h1>
        <div className="mt-4 flex flex-col gap-2 text-sm">
          <div className="flex items-center gap-3">
            <span className="w-20 shrink-0 text-muted-foreground">이메일</span>
            <span>{me?.email ?? "—"}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-20 shrink-0 text-muted-foreground">가입일</span>
            <span>
              {me?.created_at
                ? new Date(me.created_at).toLocaleDateString("ko-KR")
                : "—"}
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
            const account = accounts.find((a) => a.platform === p.key);
            const connected = !!account;
            const isOpen = openForm === p.key;
            const form = getForm(p.key);
            const available = p.kakaoLogin;

            return (
              <li key={p.key} className="flex flex-col">
                <div className="flex items-center justify-between rounded-xl border border-border bg-background px-5 py-4"
                  style={{ borderBottomLeftRadius: isOpen ? 0 : undefined, borderBottomRightRadius: isOpen ? 0 : undefined }}>
                  <div className="flex items-center gap-3">
                    <span
                      className="size-3 rounded-full"
                      style={{
                        background: connected ? p.color : "transparent",
                        border: connected ? "none" : `1.5px solid ${p.color}`,
                      }}
                    />
                    <span className="text-sm font-medium">{p.label}</span>
                    {!available && (
                      <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
                        지원 예정
                      </span>
                    )}
                    {connected && (
                      <span className="text-xs text-green-600 font-medium">연결됨</span>
                    )}
                  </div>
                  {available ? (
                    connected ? (
                      <button
                        type="button"
                        disabled={disconnecting === account.id}
                        onClick={() => handleDisconnect(account.id)}
                        className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-muted disabled:opacity-50"
                      >
                        {disconnecting === account.id ? "해제 중…" : "연결 해제"}
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setOpenForm(isOpen ? null : p.key)}
                        className="rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
                      >
                        계정 연결
                      </button>
                    )
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </div>

                {/* 카카오 로그인 폼 */}
                {isOpen && !connected && (
                  <div className="rounded-b-xl border border-t-0 border-border bg-muted/30 px-5 py-4">
                    <p className="mb-3 text-xs font-medium text-foreground">
                      카카오 계정으로 {p.label}에 연결합니다
                    </p>
                    <div className="flex flex-col gap-2">
                      <input
                        type="email"
                        placeholder="카카오 이메일"
                        value={form.email}
                        onChange={(e) => setForm(p.key, { email: e.target.value })}
                        className="h-9 rounded-lg border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                      />
                      <input
                        type="password"
                        placeholder="카카오 비밀번호"
                        value={form.password}
                        onChange={(e) => setForm(p.key, { password: e.target.value })}
                        onKeyDown={(e) => e.key === "Enter" && handleConnect(p.key)}
                        className="h-9 rounded-lg border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                      />
                    </div>
                    {form.error && (
                      <p className="mt-2 text-xs text-destructive">{form.error}</p>
                    )}
                    <p className="mt-2 text-[11px] text-muted-foreground">
                      비밀번호는 로그인에만 사용되며 저장되지 않습니다.
                    </p>
                    <button
                      type="button"
                      disabled={form.loading}
                      onClick={() => handleConnect(p.key)}
                      className="mt-3 w-full rounded-lg bg-[#FEE500] py-2 text-sm font-semibold text-[#191919] transition-opacity hover:opacity-90 disabled:opacity-50"
                    >
                      {form.loading ? "로그인 중… (최대 30초)" : "카카오로 연결하기"}
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </section>
    </main>
  );
}
