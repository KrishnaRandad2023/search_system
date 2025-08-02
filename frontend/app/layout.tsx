import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Flipkart Search - Advanced AI-Powered E-commerce Search",
  description:
    "Experience next-generation e-commerce search with intelligent autosuggest, semantic search, and ML-powered ranking - Built for Flipkart Grid 7.0",
  keywords:
    "flipkart, search, ai, ml, ecommerce, autosuggest, semantic search, grid 7.0",
  authors: [{ name: "Flipkart Grid 7.0 Team" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} antialiased bg-gray-50 font-sans`}>
        {children}
      </body>
    </html>
  );
}
