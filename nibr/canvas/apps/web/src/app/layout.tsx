import type { Metadata } from "next";
import "./globals.css";
import { Inter } from "next/font/google";
import { cn } from "@/lib/utils";
import { NuqsAdapter } from "nuqs/adapters/next/app";

// Initialize LangChain configuration early
import "@/lib/langchain-config";

const inter = Inter({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NIBR Biomni Canvas",
  description: "NIBR Biomni Canvas Chat UX",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-screen">
      <body className={cn("min-h-full", inter.className)}>
        <NuqsAdapter>{children}</NuqsAdapter>
      </body>
    </html>
  );
}
