import type { ReactNode } from "react";

interface Props {
  kind: "success" | "error" | "notice";
  children: ReactNode;
}

export function Banner({ kind, children }: Props) {
  return (
    <p role={kind === "error" ? "alert" : "status"} className={`banner ${kind}`}>
      {children}
    </p>
  );
}
