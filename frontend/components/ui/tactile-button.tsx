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
      return "bg-[var(--accent)] text-[var(--accent-foreground)] shadow-[4px_4px_8px_rgba(166,50,60,0.4),-4px_-4px_8px_rgba(255,100,110,0.4)] hover:brightness-105";
    case "ghost":
      return "bg-transparent text-[var(--foreground-muted)] hover:bg-[rgba(255,255,255,0.7)] hover:text-[var(--foreground)] hover:shadow-[var(--shadow-recessed)]";
    default:
      return "bg-[var(--background)] text-[var(--foreground)] shadow-[var(--shadow-card)] hover:text-[var(--accent)]";
  }
}

const sharedClasses =
  "inline-flex min-h-12 items-center justify-center rounded-[var(--radius-lg)] px-5 py-3 text-xs font-bold uppercase tracking-[0.18em] transition-all duration-200 ease-out active:translate-y-[2px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--background)]";

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
  return (
    <button className={classes} type="button" {...buttonProps}>
      {children}
    </button>
  );
}
