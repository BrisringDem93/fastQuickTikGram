import { cn } from "@/lib/utils";

interface ProgressBarProps {
  value: number; // 0–100
  className?: string;
  label?: string;
  showLabel?: boolean;
  color?: "brand" | "green" | "red" | "yellow";
}

const COLOR_CLASSES = {
  brand: "bg-brand-600",
  green: "bg-green-500",
  red: "bg-red-500",
  yellow: "bg-yellow-400",
};

export function ProgressBar({
  value,
  className,
  label,
  showLabel = false,
  color = "brand",
}: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div className={cn("w-full", className)}>
      {(label || showLabel) && (
        <div className="mb-1 flex items-center justify-between text-xs text-gray-500">
          {label && <span>{label}</span>}
          {showLabel && <span>{clamped}%</span>}
        </div>
      )}
      <div
        className="h-2 w-full overflow-hidden rounded-full bg-gray-200"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300",
            COLOR_CLASSES[color],
          )}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
