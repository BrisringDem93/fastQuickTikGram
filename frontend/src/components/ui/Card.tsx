import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  header?: React.ReactNode;
  footer?: React.ReactNode;
}

export function Card({ children, className, header, footer }: CardProps) {
  return (
    <div className={cn("card", className)}>
      {header && (
        <div className="border-b border-gray-100 px-6 py-4">{header}</div>
      )}
      <div className={cn(!header && !footer ? "" : "px-6 py-5")}>{children}</div>
      {footer && (
        <div className="border-t border-gray-100 px-6 py-4 bg-gray-50 rounded-b-xl">
          {footer}
        </div>
      )}
    </div>
  );
}
