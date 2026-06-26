"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { googleLogin, setToken } from "@/lib/api";

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";

// Google Identity Services 전역
interface GoogleIdConfig {
  client_id: string;
  callback: (resp: { credential: string }) => void;
}
interface GoogleButtonOptions {
  theme?: string;
  size?: string;
  width?: number;
  text?: string;
  shape?: string;
}
interface GoogleAccountsId {
  initialize: (config: GoogleIdConfig) => void;
  renderButton: (el: HTMLElement, options: GoogleButtonOptions) => void;
}
declare global {
  interface Window {
    google?: { accounts: { id: GoogleAccountsId } };
  }
}

export default function LoginPage() {
  const router = useRouter();
  const btnRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!CLIENT_ID) {
      setError("NEXT_PUBLIC_GOOGLE_CLIENT_ID 가 설정되지 않았어요. (.env.local 확인)");
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      const gid = window.google?.accounts.id;
      if (!gid) return;
      gid.initialize({
        client_id: CLIENT_ID,
        callback: async (resp) => {
          try {
            const { access_token } = await googleLogin(resp.credential);
            setToken(access_token);
            router.push("/");
          } catch {
            setError("로그인에 실패했어요. 잠시 후 다시 시도해주세요.");
          }
        },
      });
      if (btnRef.current) {
        gid.renderButton(btnRef.current, {
          theme: "outline",
          size: "large",
          width: 320,
          text: "continue_with",
          shape: "pill",
        });
      }
    };
    document.body.appendChild(script);
    return () => {
      script.remove();
    };
  }, [router]);

  return (
    <main className="mx-auto flex w-full max-w-[400px] flex-col items-center px-4 py-16 text-center">
      <h1 className="text-2xl font-bold">로그인</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Google 계정으로 시작하세요
      </p>

      {/* Google 로그인 버튼이 여기에 렌더링됨 */}
      <div ref={btnRef} className="mt-8 flex min-h-[44px] justify-center" />

      {error && <p className="mt-4 text-xs text-destructive">{error}</p>}

      <p className="mt-6 px-2 text-xs leading-relaxed text-muted-foreground">
        로그인 시 ParaPara의{" "}
        <Link href="/terms" className="underline underline-offset-2">이용약관</Link> 및{" "}
        <Link href="/privacy" className="underline underline-offset-2">개인정보 처리방침</Link>
        에 동의하게 됩니다.
      </p>
    </main>
  );
}
