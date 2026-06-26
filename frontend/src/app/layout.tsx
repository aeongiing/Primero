import type { Metadata } from "next";
import { Geist } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geist = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Primero — 중고 의류 통합 자동 판매",
  description: "사진 한 장으로 당근·번개·Fruits·차란·eBay 동시 등록",
};

const NAV_LINKS = [
  { href: "/upload", label: "상품 등록" },
  { href: "/products", label: "내 상품" },
  { href: "/dashboard", label: "대시보드" },
  { href: "/settings", label: "설정" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className={`${geist.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <header className="border-b">
          <nav className="mx-auto max-w-4xl px-4 h-14 flex items-center justify-between">
            <Link href="/" className="font-bold text-lg tracking-tight">
              Primero
            </Link>
            <ul className="flex items-center gap-6 text-sm">
              {NAV_LINKS.map(({ href, label }) => (
                <li key={href}>
                  <Link href={href} className="text-muted-foreground hover:text-foreground transition-colors">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </header>
        <div className="flex-1">{children}</div>
      </body>
    </html>
  );
}
