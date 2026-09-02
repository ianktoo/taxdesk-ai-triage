import type { ReactNode } from "react";

interface Props {
  kind: "success" | "error" | "notice";
  children: ReactNode;
}

const CLASS_BY_KIND: Record<Props["kind"], string> = {
  success: "ready",
  error: "review",
  notice: "review",
};

export function Banner({ kind, children }: Props) {
  return (
    <p
      role={kind === "error" ? "alert" : "status"}
      className={`status-badge ${CLASS_BY_KIND[kind]}`}
      style={{ display: "block", marginBottom: "var(--space-md)" }}
    >
      {children}
    </p>
  );
}
