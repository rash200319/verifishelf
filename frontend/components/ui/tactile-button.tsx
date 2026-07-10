import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactElement, ReactNode } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost";

type SharedProps = {
  variant?: Variant;
  className?: string;
  children: ReactNode;
};

type ButtonProps = SharedProps & ButtonHTMLAttributes<HTMLButtonElement> & { href?: never };
type AnchorProps = SharedProps & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> & { href: string };

function variantClassName(variant: Variant) {
  switch (variant) {
    case "primary":
      return "border border-transparent bg-[var(--accent)] text-[var(--accent-foreground)] hover:bg-[var(--accent-hover)]";
    case "ghost":
      return "border border-transparent bg-transparent text-[var(--foreground-muted)] hover:bg-[var(--panel-muted)] hover:text-[var(--foreground)]";
    default:
      return "border border-[var(--border)] bg-[var(--panel)] text-[var(--foreground)] hover:border-[var(--border-strong)] hover:bg-[var(--panel-muted)]";
  }
}

const sharedClasses =
  "inline-flex min-h-10 items-center justify-center rounded-[var(--radius-md)] px-4 py-2.5 text-sm font-medium transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--background)]";

export function TactileButton(props: ButtonProps): ReactElement;
export function TactileButton(props: AnchorProps): ReactElement;
export function TactileButton({
  variant = "secondary",
  className,
  children,
  href,
  ...rest
}: ButtonProps | AnchorProps) {
  const classes = cn(sharedClasses, variantClassName(variant), className);

  if (href) {
    const anchorProps = rest as Omit<AnchorProps, keyof SharedProps | "href">;
    return (
      <a className={classes} {...anchorProps} href={href}>
        {children}
      </a>
    );
  }

  const buttonProps = rest as Omit<ButtonProps, keyof SharedProps>;
  const type = (buttonProps as ButtonHTMLAttributes<HTMLButtonElement>).type ?? "button";
  return (
    <button className={classes} type={type} {...buttonProps}>
      {children}
    </button>
  );
}
