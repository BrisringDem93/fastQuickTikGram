"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import {
  Video,
  Zap,
  Globe,
  TrendingUp,
  Shield,
  ArrowRight,
  CheckCircle,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/Button";

const features = [
  {
    icon: Video,
    title: "Smart Video Upload",
    description:
      "Upload your raw footage and we handle transcription, processing, and storage automatically.",
  },
  {
    icon: Zap,
    title: "AI-Powered Hooks",
    description:
      "Our AI analyses your content and generates compelling hooks designed to maximise watch time and engagement.",
  },
  {
    icon: Globe,
    title: "Multi-Platform Publishing",
    description:
      "Publish to YouTube, TikTok, Instagram, and Facebook simultaneously with one click.",
  },
  {
    icon: TrendingUp,
    title: "Optimised for Virality",
    description:
      "Every hook is scored and ranked to help you choose the one most likely to go viral.",
  },
  {
    icon: Shield,
    title: "Secure & Private",
    description:
      "Your content is encrypted at rest and in transit. You own your data — always.",
  },
];

const testimonials = [
  {
    name: "Jordan M.",
    handle: "@jordancreates",
    body: "My average view count tripled in the first month. The AI hooks are scarily good.",
    avatar: "J",
  },
  {
    name: "Priya S.",
    handle: "@priyabeauty",
    body: "I used to spend hours editing captions for each platform. Now it takes 5 minutes.",
    avatar: "P",
  },
  {
    name: "Carlos V.",
    handle: "@cvfitness",
    body: "The scheduling feature alone is worth it. I set it and forget it while the views roll in.",
    avatar: "C",
  },
];

export default function LandingPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-white">
      {/* ── Nav ── */}
      <nav className="sticky top-0 z-50 border-b border-gray-100 bg-white/80 backdrop-blur">
        <div className="page-container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900">
              FastQuickTikGram
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm font-medium text-gray-600 hover:text-gray-900"
            >
              Sign in
            </Link>
            <Link href="/register">
              <Button size="sm">Get Started Free</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-50 via-white to-violet-50 px-4 pb-24 pt-20 text-center sm:pb-32 sm:pt-28">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-brand-100/40 via-transparent to-transparent" />
        <div className="relative page-container mx-auto max-w-3xl">
          <span className="mb-6 inline-flex items-center gap-1.5 rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-700">
            <Zap className="h-3 w-3" /> AI-powered content creation
          </span>
          <h1 className="mb-6 text-5xl font-extrabold leading-tight tracking-tight text-gray-900 sm:text-6xl">
            Turn any video into{" "}
            <span className="bg-gradient-to-r from-brand-600 to-violet-600 bg-clip-text text-transparent">
              viral content
            </span>
          </h1>
          <p className="mb-10 text-xl text-gray-600 text-balance">
            Upload once. Generate AI hooks. Publish everywhere — YouTube,
            TikTok, Instagram, and Facebook — in minutes.
          </p>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link href="/register">
              <Button size="lg" className="w-full sm:w-auto">
                Start for free <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                Sign in to your account
              </Button>
            </Link>
          </div>
          <p className="mt-5 text-sm text-gray-400">
            No credit card required · Free plan available
          </p>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-24 px-4">
        <div className="page-container">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
              Everything you need to grow
            </h2>
            <p className="mt-4 text-lg text-gray-500">
              A complete workflow from raw footage to published post.
            </p>
          </div>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div
                key={f.title}
                className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm transition hover:shadow-md"
              >
                <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50">
                  <f.icon className="h-5 w-5 text-brand-600" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-gray-900">
                  {f.title}
                </h3>
                <p className="text-sm leading-relaxed text-gray-500">
                  {f.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="bg-gray-50 py-24 px-4">
        <div className="page-container">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
              From upload to viral in 5 steps
            </h2>
          </div>
          <div className="mx-auto max-w-2xl space-y-6">
            {[
              "Upload your video — mp4, mov, avi, or mkv up to 500 MB",
              "AI transcribes and generates 3+ hook options ranked by viral score",
              "Approve or edit your favourite hook",
              "Select which platforms to publish to",
              "Publish instantly or schedule for the perfect time",
            ].map((step, i) => (
              <div key={i} className="flex items-start gap-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">
                  {i + 1}
                </div>
                <p className="pt-1 text-base text-gray-700">{step}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Testimonials ── */}
      <section className="py-24 px-4">
        <div className="page-container">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
              Loved by creators
            </h2>
          </div>
          <div className="grid gap-8 sm:grid-cols-3">
            {testimonials.map((t) => (
              <div
                key={t.name}
                className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm"
              >
                <p className="mb-5 text-sm leading-relaxed text-gray-600">
                  "{t.body}"
                </p>
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">
                    {t.avatar}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      {t.name}
                    </p>
                    <p className="text-xs text-gray-400">{t.handle}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="bg-gradient-to-r from-brand-600 to-violet-600 py-20 px-4 text-center text-white">
        <div className="page-container mx-auto max-w-2xl">
          <h2 className="mb-4 text-3xl font-bold">
            Ready to 10× your content output?
          </h2>
          <p className="mb-8 text-brand-100">
            Join thousands of creators already using FastQuickTikGram.
          </p>
          <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Link href="/register">
              <Button
                size="lg"
                className="w-full bg-white text-brand-700 hover:bg-gray-50 sm:w-auto"
              >
                Create your free account
              </Button>
            </Link>
          </div>
          <ul className="mt-6 flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-brand-100">
            {[
              "Free forever plan",
              "No credit card",
              "Cancel anytime",
            ].map((item) => (
              <li key={item} className="flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-gray-100 py-10 px-4 text-center text-sm text-gray-400">
        <p>© {new Date().getFullYear()} FastQuickTikGram. All rights reserved.</p>
      </footer>
    </div>
  );
}
