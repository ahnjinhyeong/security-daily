import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Security Daily | Morning Security Briefing",
  description: "매일 핵심 보안뉴스를 요약하고 분석하며 Quiz로 복습하는 보안 지식 Dashboard",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ko" className={`${geistSans.variable} ${geistMono.variable}`}><body>{children}</body></html>;
}
