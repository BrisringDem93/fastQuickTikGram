import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type SpinnerSize = "sm" | "md" | "lg" | "xl";

interface LoadingSpinnerProps {
  size?: SpinnerSize;
  className?: string;
  label?: string;
}

const SIZE_CLASSES: Record<SpinnerSize, string> = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-8 w-8",
  xl: "h-12 w-12",
};

export function LoadingSpinner({
  size = "md",
  className,
  label,
}: LoadingSpinnerProps) {
  return (
    <div className={cn("flex flex-col items-center gap-2", className)} role="status">
      <Loader2
        className={cn("animate-spin text-brand-600", SIZE_CLASSES[size])}
        aria-hidden="true"
      />
      {label && <p className="text-sm text-gray-500">{label}</p>}
      <span className="sr-only">{label ?? "Loading…"}</span>
    </div>
  );
}
