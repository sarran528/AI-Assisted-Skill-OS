import type { ButtonHTMLAttributes } from "react";

interface BrutalButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
}

export function BrutalButton({
  variant = "secondary",
  className,
  children,
  ...rest
}: BrutalButtonProps) {
  return (
    <button
      {...rest}
      className={`brutal-button brutal-button--${variant} ${className ?? ""}`.trim()}
    >
      {children}
    </button>
  );
}
