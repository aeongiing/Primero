import Link from "next/link";

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62Z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18Z"
      />
      <path
        fill="#FBBC05"
        d="M3.97 10.72a5.4 5.4 0 0 1 0-3.44V4.95H.96a9 9 0 0 0 0 8.1l3.01-2.33Z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58A9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58Z"
      />
    </svg>
  );
}

export default function LoginPage() {
  return (
    <main className="mx-auto w-full max-w-[400px] px-4 py-12">
      <h1 className="text-center text-2xl font-bold">로그인</h1>

      {/* 이메일 / 비밀번호 폼 — 화면 구성 일치용. 실제 인증은 Google 단일.
          (정책: Google OAuth만 지원 → 이 폼은 추후 제거 가능) */}
      <form className="mt-10 flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label htmlFor="email" className="text-sm font-medium">
            이메일
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            className="h-12 rounded-md border border-input px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="password" className="text-sm font-medium">
            비밀번호
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            className="h-12 rounded-md border border-input px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <button
          type="submit"
          className="h-12 rounded-md bg-primary text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
        >
          로그인
        </button>

        <Link
          href="/login"
          className="mx-auto text-xs text-muted-foreground underline underline-offset-2"
        >
          회원 가입
        </Link>
      </form>

      {/* 소셜 로그인 — Google 단일 (Facebook/Kakao 미지원) */}
      <div className="mt-6 flex flex-col gap-3">
        <a
          href="/api/v1/auth/google"
          className="flex h-12 w-full items-center justify-center gap-2.5 rounded-full border border-border bg-white text-sm font-medium transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <GoogleIcon />
          Google로 계속하기
        </a>
      </div>
    </main>
  );
}
