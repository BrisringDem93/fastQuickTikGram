import { forwardRef } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "outline" | "danger" | "ghost";
type ButtonSize = "xs" | "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  children: React.ReactNode;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-brand-600 text-white hover:bg-brand-700 focus:ring-brand-500 disabled:opacity-60",
  secondary:
    "bg-gray-100 text-gray-700 hover:bg-gray-200 focus:ring-gray-400 disabled:opacity-60",
  outline:
    "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-brand-500 disabled:opacity-60",
  danger:
    "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 disabled:opacity-60",
  ghost:
    "bg-transparent text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus:ring-gray-400 disabled:opacity-60",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  xs: "px-2.5 py-1.5 text-xs gap-1",
  sm: "px-3 py-2 text-sm gap-1.5",
  md: "px-4 py-2.5 text-sm gap-2",
  lg: "px-5 py-3 text-base gap-2",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      isLoading = false,
      disabled,
      className,
      children,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center rounded-lg font-medium",
          "focus:outline-none focus:ring-2 focus:ring-offset-2",
          "transition-colors disabled:cursor-not-allowed",
          VARIANT_CLASSES[variant],
          SIZE_CLASSES[size],
          className,
        )}
        {...props}
      >
        {isLoading && (
          <Loader2 className="animate-spin shrink-0" style={{ width: "1em", height: "1em" }} />
        )}
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
