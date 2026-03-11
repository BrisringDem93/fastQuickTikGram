import { cn } from "@/lib/utils";

export type BadgeColor =
  | "gray"
  | "green"
  | "red"
  | "yellow"
  | "blue"
  | "orange"
  | "purple";

interface BadgeProps {
  children: React.ReactNode;
  color?: BadgeColor | string;
  className?: string;
}

const COLOR_CLASSES: Record<string, string> = {
  gray: "bg-gray-100 text-gray-600",
  green: "bg-green-100 text-green-700",
  red: "bg-red-100 text-red-700",
  yellow: "bg-yellow-100 text-yellow-700",
  blue: "bg-blue-100 text-blue-700",
  orange: "bg-orange-100 text-orange-700",
  purple: "bg-purple-100 text-purple-700",
};

export function Badge({ children, color = "gray", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        COLOR_CLASSES[color] ?? COLOR_CLASSES.gray,
        className,
      )}
    >
      {children}
    </span>
  );
}
