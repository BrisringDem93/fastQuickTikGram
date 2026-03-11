"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useJob } from "@/lib/queries";
import { JobStatus } from "@/types";
import { WizardLayout } from "@/components/wizard/WizardLayout";
import { StepUploadVideo } from "@/components/wizard/StepUploadVideo";
import { StepGenerateHooks } from "@/components/wizard/StepGenerateHooks";
import { StepApproveHook } from "@/components/wizard/StepApproveHook";
import { StepSelectDestinations } from "@/components/wizard/StepSelectDestinations";
import { StepPublishOrSchedule } from "@/components/wizard/StepPublishOrSchedule";
import { SocialConnectModal } from "@/components/wizard/SocialConnectModal";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

function resolveWizardStep(status: JobStatus): number {
  switch (status) {
    case JobStatus.PENDING_UPLOAD:
    case JobStatus.UPLOAD_IN_PROGRESS:
      return 1;
    case JobStatus.UPLOAD_COMPLETE:
    case JobStatus.TRANSCRIPTION_IN_PROGRESS:
    case JobStatus.TRANSCRIPTION_COMPLETE:
    case JobStatus.HOOK_GENERATION_IN_PROGRESS:
    case JobStatus.HOOK_GENERATION_COMPLETE:
      return 2;
    case JobStatus.HOOK_APPROVED:
      return 3;
    case JobStatus.WAITING_FOR_SOCIAL_CONNECTION:
    case JobStatus.DESTINATIONS_SELECTED:
      return 4;
    case JobStatus.PUBLISHING_IN_PROGRESS:
    case JobStatus.PARTIALLY_PUBLISHED:
    case JobStatus.PUBLISHED:
    case JobStatus.SCHEDULED:
    case JobStatus.FAILED:
    case JobStatus.CANCELLED:
      return 5;
    default:
      return 1;
  }
}

export default function JobPage() {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const { data: job, isLoading: jobLoading, error } = useJob(id);
  const [showSocialModal, setShowSocialModal] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  // Show social connection modal automatically when job reaches that state
  useEffect(() => {
    if (job?.status === JobStatus.WAITING_FOR_SOCIAL_CONNECTION) {
      setShowSocialModal(true);
    }
  }, [job?.status]);

  if (authLoading || jobLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 text-center">
        <p className="text-lg font-semibold text-gray-900">Job not found</p>
        <p className="text-sm text-gray-500">
          This job may have been deleted or you don't have access.
        </p>
        <button
          onClick={() => router.push("/dashboard")}
          className="text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          ← Back to dashboard
        </button>
      </div>
    );
  }

  const currentStep = resolveWizardStep(job.status);

  return (
    <>
      <WizardLayout job={job} currentStep={currentStep}>
        {currentStep === 1 && <StepUploadVideo job={job} />}
        {currentStep === 2 && <StepGenerateHooks job={job} />}
        {currentStep === 3 && <StepApproveHook job={job} />}
        {currentStep === 4 && (
          <StepSelectDestinations
            job={job}
            onOpenSocialModal={() => setShowSocialModal(true)}
          />
        )}
        {currentStep === 5 && <StepPublishOrSchedule job={job} />}
      </WizardLayout>

      {showSocialModal && (
        <SocialConnectModal
          onClose={() => setShowSocialModal(false)}
          jobId={id}
        />
      )}
    </>
  );
}
