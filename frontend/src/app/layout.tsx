import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

import { Header, Footer } from "@/components/shell";
import { getAsOfDate } from "@/lib/api";

// Every route reads the live API per request; never prerender build-time data.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "OPEN PSX — Shariah Market Intelligence",
  description:
    "Education-first market-intelligence web app for KMI-30 stocks and PSX-listed ETFs.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const asOfDate = await getAsOfDate();

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="flex min-h-full flex-col bg-background text-foreground">
        <Header asOfDate={asOfDate} />
        <main className="flex-1 w-full">{children}</main>
        <Footer asOfDate={asOfDate} />
      </body>
    </html>
  );
}
