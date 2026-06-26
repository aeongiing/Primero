import type { Metadata } from "next";
import { Lobster } from "next/font/google";
import "./globals.css";
import SiteHeader from "@/components/layout/site-header";

const logoFont = Lobster({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-logo",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ParaPara — 중고 의류 통합 자동 판매",
  description: "사진 한 장으로 당근·번개·Fruits·차란·eBay 동시 등록",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className={`${logoFont.variable} h-full antialiased`}>
      <head>
        <link
          rel="stylesheet"
          as="style"
          crossOrigin="anonymous"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css"
        />
      </head>
      <body className="min-h-full flex flex-col">
        <SiteHeader />
        <div className="flex-1">{children}</div>
      </body>
    </html>
  );
}
