"use client";

import React, { useState } from "react";
import { Download, FileJson, FileText, Share2, Check } from "lucide-react";
import { getExportJsonUrl, getExportMdUrl } from "@/lib/api";

interface ExportControlsProps {
  sessionId: string;
}

export const ExportControls: React.FC<ExportControlsProps> = ({ sessionId }) => {
  const [copied, setCopied] = useState(false);

  const handleCopyLink = () => {
    const url = `${window.location.origin}?session_id=${sessionId}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <a
        href={getExportJsonUrl(sessionId)}
        download
        className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-700 transition"
      >
        <FileJson className="h-3.5 w-3.5 text-blue-400" />
        <span>Export JSON</span>
      </a>

      <a
        href={getExportMdUrl(sessionId)}
        download
        className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-700 transition"
      >
        <FileText className="h-3.5 w-3.5 text-cyan-400" />
        <span>Export Markdown</span>
      </a>

      <button
        type="button"
        onClick={handleCopyLink}
        className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-700 transition"
      >
        {copied ? (
          <>
            <Check className="h-3.5 w-3.5 text-emerald-400" />
            <span className="text-emerald-300">Link Copied!</span>
          </>
        ) : (
          <>
            <Share2 className="h-3.5 w-3.5 text-purple-400" />
            <span>Share Report Link</span>
          </>
        )}
      </button>
    </div>
  );
};
