import type { Metadata } from "next";
import { Inter, Outfit, Fira_Code } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  display: "swap",
});

const firaCode = Fira_Code({
  variable: "--font-fira-code",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "SureFact - Autonomous Research Agent",
  description: "Deep multi-layer academic research agent",
};

import { ClerkProvider } from "@clerk/nextjs";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body
          className={`${inter.variable} ${outfit.variable} ${firaCode.variable} font-sans antialiased text-white bg-black selection:bg-cyan-500/30 selection:text-cyan-200`}
        >
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
