/**
 * CvMarkdownEditor.tsx
 *
 * Full-screen modal with two panes:
 *   Left  — editable Markdown textarea (the source of truth)
 *   Right — live HTML preview styled exactly as the final PDF will look
 *
 * The user edits the Markdown and sees the rendered result in real-time.
 * "Download PDF" triggers window.print() on a hidden print-only frame that
 * contains only the preview pane — the browser's own PDF engine handles
 * fonts, line-wrapping and page breaks correctly.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { X, Download, FileText } from 'lucide-react';

// ---------------------------------------------------------------------------
// Minimal Markdown → HTML renderer
// No external dependency. Covers the subset produced by cv_to_markdown.ts.
// ---------------------------------------------------------------------------

function mdToHtml(md: string): string {
  const lines = md.split('\n');
  const out: string[] = [];
  let inList = false;

  const closeList = () => {
    if (inList) { out.push('</ul>'); inList = false; }
  };

  const escape = (s: string) =>
    s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

  const inline = (s: string) =>
    escape(s)
      .replaceAll(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replaceAll(/\*(.+?)\*/g, '<em>$1</em>');

  for (const raw of lines) {
    const line = raw;

    // H1 — candidate name
    if (line.startsWith('# ')) {
      closeList();
      out.push(`<h1>${inline(line.slice(2))}</h1>`);
      continue;
    }

    // H2 — section heading
    if (line.startsWith('## ')) {
      closeList();
      out.push(`<h2>${inline(line.slice(3))}</h2>`);
      continue;
    }

    // HR — separator below contact line
    if (/^---+$/.test(line.trim())) {
      closeList();
      out.push('<hr class="header-rule" />');
      continue;
    }

    // Bullet list item
    if (line.startsWith('- ')) {
      if (!inList) { out.push('<ul>'); inList = true; }
      out.push(`<li>${inline(line.slice(2))}</li>`);
      continue;
    }

    // Blank line
    if (line.trim() === '') {
      closeList();
      out.push('<div class="spacer"></div>');
      continue;
    }

    // Paragraph / contact line / entry body
    closeList();
    out.push(`<p>${inline(line)}</p>`);
  }

  closeList();
  return out.join('\n');
}

// ---------------------------------------------------------------------------
// Print stylesheet injected into the print iframe
// This is what actually becomes the PDF — browser engine renders it.
// ---------------------------------------------------------------------------

const PRINT_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Inter', Helvetica, Arial, sans-serif;
    font-size: 9.5pt;
    line-height: 1.5;
    color: #121214;
    background: white;
    padding: 16mm 16mm 14mm;
    max-width: 210mm;
    margin: 0 auto;
  }

  h1 {
    font-size: 21pt;
    font-weight: 700;
    letter-spacing: 0.02em;
    color: #121214;
    margin-bottom: 3pt;
  }

  p { margin-bottom: 3pt; color: #646473; font-size: 8.5pt; }
  p + p { margin-top: 0; }

  hr.header-rule {
    border: none;
    border-top: 0.7pt solid #4f46e5;
    margin: 6pt 0 10pt;
  }

  h2 {
    font-size: 9.5pt;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #4f46e5;
    margin-top: 10pt;
    margin-bottom: 2pt;
    text-transform: uppercase;
    border-bottom: 0.3pt solid #d2d2dc;
    padding-bottom: 3pt;
  }

  strong { font-weight: 700; color: #121214; font-size: 9pt; display: block; margin-top: 6pt; }

  ul {
    list-style: none;
    padding: 0;
    margin: 3pt 0 3pt 10pt;
  }

  li {
    position: relative;
    padding-left: 8pt;
    margin-bottom: 2pt;
    font-size: 8.8pt;
    color: #121214;
    line-height: 1.45;
  }

  li::before {
    content: '•';
    position: absolute;
    left: 0;
    color: #121214;
  }

  .spacer { height: 3pt; }

  @media print {
    body { padding: 0; }
    @page { size: A4; margin: 16mm 16mm 14mm; }
  }
`;

// ---------------------------------------------------------------------------
// Preview CSS — matches PRINT_CSS but lives in the app (dark bg strip removed)
// ---------------------------------------------------------------------------

const PREVIEW_CSS = `
  <style>
    ${PRINT_CSS}
    body { background: white; }
  </style>
`;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface CvMarkdownEditorProps {
  readonly initialMarkdown: string;
  readonly candidateName: string;
  readonly onClose: () => void;
}

export function CvMarkdownEditor({
  initialMarkdown,
  candidateName,
  onClose,
}: CvMarkdownEditorProps) {
  const [markdown, setMarkdown] = useState(initialMarkdown);
  const previewRef = useRef<HTMLIFrameElement>(null);
  const printFrameRef = useRef<HTMLIFrameElement | null>(null);

  // Update the preview iframe whenever Markdown changes
  useEffect(() => {
    const iframe = previewRef.current;
    if (!iframe) return;
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8">${PREVIEW_CSS}</head><body>${mdToHtml(markdown)}</body></html>`;
    iframe.srcdoc = html;
  }, [markdown]);

  // Print-to-PDF via a hidden iframe so only the CV content prints
  const handleDownload = useCallback(() => {
    // Remove any previous print frame
    if (printFrameRef.current) {
      printFrameRef.current.remove();
    }

    const frame = document.createElement('iframe');
    frame.style.cssText = 'position:fixed;width:0;height:0;border:none;left:-9999px;top:-9999px;';
    document.body.appendChild(frame);
    printFrameRef.current = frame;

    const doc = frame.contentDocument;
    if (!doc) return;
    doc.open();
    doc.close();
    // Write via innerHTML on the documentElement to avoid deprecated doc.write
    doc.documentElement.innerHTML = `<head><meta charset="utf-8"><title>${candidateName} — CV</title><style>${PRINT_CSS}</style></head><body>${mdToHtml(markdown)}</body>`;

    frame.contentWindow?.focus();
    // Short timeout lets the iframe fonts load before printing
    setTimeout(() => {
      frame.contentWindow?.print();
    }, 400);
  }, [markdown, candidateName]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    globalThis.addEventListener('keydown', handler);
    return () => globalThis.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[#0e0e10]">
      {/* ── Toolbar ────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-white/10 shrink-0">
        <div className="flex items-center gap-2 text-white/80 font-semibold text-sm">
          <FileText className="w-4 h-4 text-accent" />
          Edit & Preview CV
          <span className="text-white/30 font-normal ml-2 text-xs">
            Edit Markdown on the left · live preview on the right
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 bg-accent text-white font-semibold rounded-lg text-sm hover:bg-indigo-400 transition-colors"
          >
            <Download className="w-4 h-4" />
            Download PDF
          </button>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-white/50 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Close editor"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* ── Split pane ─────────────────────────────────────────────────── */}
      <div className="flex flex-1 min-h-0 divide-x divide-white/10">
        {/* Left — Markdown editor */}
        <div className="flex flex-col w-1/2 min-w-0">
          <div className="px-4 py-2 text-xs font-mono uppercase tracking-widest text-white/30 bg-white/5 shrink-0">
            Markdown source
          </div>
          <textarea
            className="flex-1 resize-none bg-[#111113] text-white/85 font-mono text-sm p-5 outline-none leading-relaxed"
            value={markdown}
            onChange={e => setMarkdown(e.target.value)}
            spellCheck={false}
            aria-label="CV Markdown source"
          />
        </div>

        {/* Right — live preview */}
        <div className="flex flex-col w-1/2 min-w-0 bg-white">
          <div className="px-4 py-2 text-xs font-mono uppercase tracking-widest text-black/30 bg-black/5 shrink-0">
            Preview (printed as-is)
          </div>
          <iframe
            ref={previewRef}
            className="flex-1 border-none"
            title="CV Preview"
            sandbox="allow-same-origin"
          />
        </div>
      </div>
    </div>
  );
}
