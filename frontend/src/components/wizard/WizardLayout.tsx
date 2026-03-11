"use client";

import { CheckIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import type { ContentJob } from "@/types";
import { Navbar } from "@/components/layout/navbar";
import { cn } from "@/lib/utils";

interface WizardStep {
  number: number;
  label: string;
}

const STEPS: WizardStep[] = [
  { number: 1, label: "Upload" },
  { number: 2, label: "Hooks" },
  { number: 3, label: "Approve" },
  { number: 4, label: "Platforms" },
  { number: 5, label: "Publish" },
];

interface WizardLayoutProps {
  job: ContentJob;
  currentStep: number;
  children: React.ReactNode;
}

export function WizardLayout({ job, currentStep, children }: WizardLayoutProps) {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="page-container py-8">
        {/* Back link */}
        <button
          onClick={() => router.push("/dashboard")}
          className="mb-6 flex items-center gap-1.5 text-sm font-medium text-gray-500 hover:text-gray-700"
        >
          ← Back to dashboard
        </button>

        {/* Job title */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 truncate">
            {job.title}
          </h1>
          <p className="mt-1 text-sm text-gray-500">Job ID: {job.id.slice(0, 8)}&hellip;</p>
        </div>

        {/* Step indicator */}
        <div className="card mb-8 p-4">
          <nav aria-label="Progress">
            <ol className="flex items-center">
              {STEPS.map((step, idx) => {
                const isCompleted = step.number < currentStep;
                const isCurrent = step.number === currentStep;
                const isUpcoming = step.number > currentStep;

                return (
                  <li
                    key={step.number}
                    className={cn(
                      "flex flex-1 items-center",
                      idx < STEPS.length - 1 &&
                        "after:mx-2 after:h-px after:flex-1 after:content-[''] sm:after:mx-3",
                      isCompleted ? "after:bg-brand-600" : "after:bg-gray-200",
                    )}
                  >
                    <div className="flex flex-col items-center gap-1">
                      <span
                        className={cn(
                          "flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold transition-colors",
                          isCompleted &&
                            "bg-brand-600 text-white",
                          isCurrent &&
                            "border-2 border-brand-600 bg-white text-brand-700",
                          isUpcoming &&
                            "border-2 border-gray-200 bg-white text-gray-400",
                        )}
                      >
                        {isCompleted ? (
                          <CheckIcon className="h-4 w-4" />
                        ) : (
                          step.number
                        )}
                      </span>
                      <span
                        className={cn(
                          "hidden text-xs font-medium sm:block",
                          isCompleted && "text-brand-600",
                          isCurrent && "text-brand-700",
                          isUpcoming && "text-gray-400",
                        )}
                      >
                        {step.label}
                      </span>
                    </div>
                  </li>
                );
              })}
            </ol>
          </nav>
        </div>

        {/* Step content */}
        <div className="animate-fade-in">{children}</div>
      </div>
    </div>
  );
}
