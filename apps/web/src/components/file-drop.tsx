"use client";

import { useCallback, useRef, useState, type DragEvent } from "react";

type Props = {
  disabled?: boolean;
  accept?: string;
  label?: string;
  onFile: (file: File) => void;
};

/** Hostile-file drop zone (README §9.5.6). Never reads content as executable. */
export function FileDrop({
  disabled,
  accept = ".txt,.md,.html,.htm,.pdf,.docx,.eml,.json,.py,.js,.ts,.png,.jpg,.jpeg,.gif,.webp",
  label = "Drop a file here, or click to choose",
  onFile,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  const take = useCallback(
    (file: File | undefined) => {
      if (!file || disabled) return;
      onFile(file);
    },
    [disabled, onFile],
  );

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setOver(false);
    take(e.dataTransfer.files?.[0]);
  }

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      onKeyDown={(e) => {
        if (disabled) return;
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      onDragEnter={(e) => {
        e.preventDefault();
        if (!disabled) setOver(true);
      }}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      className={`rounded-panel border border-dashed px-3 py-6 text-center text-sm transition-colors ${
        over ? "border-uv bg-uv/5" : "border-rule bg-paper"
      } ${disabled ? "opacity-50 pointer-events-none" : "cursor-pointer hover:border-uv"}`}
    >
      <p className="text-ink">{label}</p>
      <p className="text-xs text-slate mt-1">
        txt · md · html · pdf · docx · eml · json · code · images · max 10 MB
      </p>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="sr-only"
        disabled={disabled}
        onChange={(e) => {
          take(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
    </div>
  );
}
