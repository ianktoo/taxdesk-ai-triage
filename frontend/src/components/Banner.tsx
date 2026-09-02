import type { ReactNode } from "react";

interface Props {
  kind: "success" | "error";
  children: ReactNode;
}

export function Banner({ kind, children }: Props) {
  return (
    <p
      role={kind === "error" ? "alert" : "status"}
      className={`status-badge ${kind === "error" ? "review" : "ready"}`}
      style={{ display: "block", marginBottom: "var(--space-md)" }}
    >
      {children}
    </p>
  );
}
