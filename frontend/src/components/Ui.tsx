import { Link } from "react-router-dom";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export function Button({ children, className = "", variant = "primary", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" | "dark" }) {
  const styles = {
    primary: "bg-lime text-pine-950 hover:bg-white",
    ghost: "border border-current bg-transparent",
    dark: "bg-pine-900 text-cream-50 hover:bg-pine-800",
  }[variant];
  return (
    <button className={`inline-flex items-center justify-center rounded-full px-5 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${styles} ${className}`} {...props}>
      {children}
    </button>
  );
}

export function TextLink({ to, children, className = "" }: { to: string; children: ReactNode; className?: string }) {
  return <Link to={to} className={`inline-flex items-center rounded-full px-5 py-3 text-sm font-semibold ${className}`}>{children}</Link>;
}

export function Field({ label, error, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string }) {
  return (
    <label className="block text-sm">
      <span className="spec text-pine-800">{label}</span>
      <input {...props} className="mt-2 w-full rounded-2xl border border-cream-200 bg-white px-4 py-3 text-ink outline-none focus:border-pine-700" />
      {error && <span className="mt-1 block text-berry">{error}</span>}
    </label>
  );
}

export function Notice({ children }: { children: ReactNode }) {
  return <p className="rounded-2xl border border-mango/40 bg-mango/10 px-4 py-3 text-sm text-ink">{children}</p>;
}
