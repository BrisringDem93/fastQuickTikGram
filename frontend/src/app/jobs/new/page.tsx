"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useCreateJob } from "@/lib/queries";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import toast from "react-hot-toast";

export default function NewJobPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const createJob = useCreateJob();

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }

    createJob
      .mutateAsync({ title: "Untitled Video" })
      .then((job) => {
        router.replace(`/jobs/${job.id}`);
      })
      .catch(() => {
        toast.error("Failed to create job. Please try again.");
        router.replace("/dashboard");
      });
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, isAuthenticated]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <LoadingSpinner size="lg" />
      <p className="text-sm text-gray-500">Creating your job…</p>
    </div>
  );
}
