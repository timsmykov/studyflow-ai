import { ClerkProvider } from "@clerk/nextjs";
import { ThemeProvider } from "@/components/theme-provider";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "StudyFlow AI - AI Tutor & Analytics",
  description: "Personalized learning paths, dropout prediction, and progress tracking",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <html lang="en" suppressHydrationWarning>
          <body className={inter.className}>{children}</body>
        </html>
      </ThemeProvider>
    </ClerkProvider>
  );
}
