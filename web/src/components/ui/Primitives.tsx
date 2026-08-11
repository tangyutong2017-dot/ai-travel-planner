import type { ReactNode } from "react";


export function WBox({
  className = "",
  children,
  onClick,
}: {
  className?: string;
  children?: ReactNode;
  onClick?: () => void;
}) {
  return (
    <div
      className={`rounded-lg border border-slate-200/80 bg-white/95 shadow-sm shadow-slate-200/50 backdrop-blur ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

export function WImgBox({ className = "", label = "图片占位" }: { className?: string; label?: string }) {
  return (
    <div className={`border border-sky-100 bg-[linear-gradient(135deg,#e0f2fe,#f0fdfa_52%,#fff7ed)] flex items-center justify-center ${className}`}>
      <span className="text-[11px] text-slate-400 font-mono">{label}</span>
    </div>
  );
}

export function WBtn({
  label,
  primary = false,
  small = false,
  className = "",
  onClick,
}: {
  label: string;
  primary?: boolean;
  small?: boolean;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md border font-medium font-mono cursor-pointer transition-all hover:-translate-y-px ${
        primary
          ? "bg-sky-600 text-white border-sky-600 shadow-sm shadow-sky-200 hover:bg-sky-700"
          : "bg-white text-slate-700 border-slate-200 hover:border-sky-200 hover:bg-sky-50"
      } ${small ? "text-[11px] px-3 py-1" : "text-[13px] px-4 py-2"} ${className}`}
    >
      {label}
    </button>
  );
}

export function WAnnotation({ text }: { text: string }) {
  return (
    <span className="font-mono text-[9px] text-slate-400 leading-none">{text}</span>
  );
}

export function Divider({ className = "" }: { className?: string }) {
  return <div className={`border-t border-slate-200 ${className}`} />;
}

export function SectionTitle({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-[13px] font-semibold text-slate-800">{text}</span>
      <div className="flex-1 border-t border-dashed border-slate-200" />
    </div>
  );
}
