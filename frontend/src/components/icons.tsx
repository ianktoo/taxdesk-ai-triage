// Small inline icon set, no external icon library needed for a handful of glyphs.
import type { SVGProps } from "react";

function Svg(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    />
  );
}

export function MailIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 7 9 6 9-6" />
    </Svg>
  );
}

export function TicketQueueIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <path d="M4 6h16" />
      <path d="M4 12h10" />
      <path d="M4 18h7" />
      <circle cx="19" cy="16" r="2.5" />
    </Svg>
  );
}

export function UploadIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <path d="M12 16V4" />
      <path d="m7 9 5-5 5 5" />
      <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
    </Svg>
  );
}

export function AuditIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <path d="M12 8v4l2.5 2.5" />
      <circle cx="12" cy="12" r="9" />
    </Svg>
  );
}

export function RecordsIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <rect x="4" y="3" width="16" height="18" rx="2" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </Svg>
  );
}

export function CheckCircleIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </Svg>
  );
}

export function FlagIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <path d="M5 3v18" />
      <path d="M5 4h11l-2.5 4L16 12H5" />
    </Svg>
  );
}

export function FileIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <path d="M7 3h7l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
      <path d="M14 3v4h4" />
    </Svg>
  );
}

export function PaperclipIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <path d="M21 12.5 12.5 21a5 5 0 0 1-7-7l8-8a3.5 3.5 0 0 1 5 5l-8 8a2 2 0 0 1-3-3l7.5-7.5" />
    </Svg>
  );
}

export function SendIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <path d="m3 11 18-8-8 18-2.5-7.5L3 11Z" />
    </Svg>
  );
}

export function SpeakerIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <path d="M4 9v6h4l5 4V5L8 9H4Z" />
      <path d="M16.5 8.5a5 5 0 0 1 0 7" />
      <path d="M19 6a8.5 8.5 0 0 1 0 12" />
    </Svg>
  );
}

export function SparkleIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
      <path d="m6 6 2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" />
    </Svg>
  );
}

export function SunIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M3 12h2M19 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
    </Svg>
  );
}

export function MoonIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Svg {...props}>
      <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z" />
    </Svg>
  );
}
