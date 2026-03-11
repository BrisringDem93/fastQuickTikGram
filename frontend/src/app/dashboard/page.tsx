"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import Link from "next/link";
import { formatDateRelative, getStatusColor, getStatusLabel } from "@/lib/utils";
import { useJobs } from "@/lib/queries";
import { Navbar } from "@/components/layout/navbar";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { useCreateJob } from "@/lib/queries";
import type { ContentJob, JobStatus } from "@/types";
import { Plus, Video, ArrowRight } from "lucide-react";
import toast from "react-hot-toast";
import { getErrorMessage } from "@/lib/utils";

function JobCard({ job }: { job: ContentJob }) {
  const color = getStatusColor(job.status as JobStatus);
  return (
    <Link
      href={`/jobs/${job.id}`}
      className="card flex items-center gap-5 p-5 transition hover:shadow-md hover:-translate-y-0.5"
    >
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-50">
        <Video className="h-6 w-6 text-brand-600" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-3">
          <h3 className="truncate text-sm font-semibold text-gray-900">
            {job.title}
          </h3>
          <Badge color={color}>{getStatusLabel(job.status as JobStatus)}</Badge>
        </div>
        <p className="mt-1 text-xs text-gray-400">
          {formatDateRelative(job.created_at)}
        </p>
      </div>
      <ArrowRight className="h-4 w-4 shrink-0 text-gray-300" />
    </Link>
  );
}

function SkeletonCard() {
  return (
    <div className="card flex items-center gap-5 p-5">
      <div className="h-12 w-12 animate-pulse rounded-xl bg-gray-100" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-2/3 animate-pulse rounded bg-gray-100" />
        <div className="h-3 w-1/3 animate-pulse rounded bg-gray-100" />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const { data: jobs, isLoading: jobsLoading, error } = useJobs();
  const createJob = useCreateJob();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  async function handleNewJob() {
    try {
      const job = await createJob.mutateAsync({ title: "Untitled Video" });
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  }

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="page-container py-10">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Your Jobs</h1>
            <p className="mt-1 text-sm text-gray-500">
              Manage and track all your video content jobs.
            </p>
          </div>
          <Button onClick={handleNewJob} isLoading={createJob.isPending}>
            <Plus className="h-4 w-4" />
            New Job
          </Button>
        </div>

        {/* Content */}
        {jobsLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : error ? (
          <div className="rounded-xl border border-red-200 bg-red-50 px-6 py-5 text-sm text-red-700">
            Failed to load jobs. Please refresh the page.
          </div>
        ) : jobs && jobs.length > 0 ? (
          <div className="space-y-3">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        ) : (
          /* Empty state */
          <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-200 bg-white py-20 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50">
              <Video className="h-8 w-8 text-brand-400" />
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900">
              No jobs yet
            </h3>
            <p className="mb-6 max-w-xs text-sm text-gray-500">
              Create your first job to start turning your videos into viral
              content across all platforms.
            </p>
            <Button onClick={handleNewJob} isLoading={createJob.isPending}>
              <Plus className="h-4 w-4" />
              Create your first job
            </Button>
          </div>
        )}
      </main>
    </div>
  );
}
