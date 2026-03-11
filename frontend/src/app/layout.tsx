import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";
import Providers from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "FastQuickTikGram – Viral Content, Effortlessly",
    template: "%s | FastQuickTikGram",
  },
  description:
    "Turn any video into viral content for YouTube, TikTok, Instagram and Facebook in minutes.",
  keywords: ["video content", "social media", "AI hooks", "content creator"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased font-sans">
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: "#1f2937",
                color: "#f9fafb",
                borderRadius: "10px",
                fontSize: "14px",
              },
              success: {
                iconTheme: { primary: "#6366f1", secondary: "#fff" },
              },
              error: {
                iconTheme: { primary: "#ef4444", secondary: "#fff" },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
