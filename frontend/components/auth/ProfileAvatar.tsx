"use client";

import Link from "next/link";

type Props = {
  firstName: string;
  lastName: string;
  size?: "sm" | "md" | "lg";
  href?: string;
  className?: string;
};

const sizeClasses = {
  sm: "h-9 w-9 text-xs",
  md: "h-11 w-11 text-sm",
  lg: "h-20 w-20 text-2xl",
};

export function ProfileAvatar({ firstName, lastName, size = "sm", href, className = "" }: Props) {
  const initials = `${(firstName || "O")[0]}${(lastName || "P")[0]}`.toUpperCase();
  const classes = `inline-flex ${sizeClasses[size]} items-center justify-center rounded-full bg-[var(--accent)] font-semibold text-white shadow-sm ${className}`;

  if (href) {
    return (
      <Link href={href} className={classes} title="Open profile" aria-label="Open profile">
        {initials}
      </Link>
    );
  }

  return <div className={classes}>{initials}</div>;
}
