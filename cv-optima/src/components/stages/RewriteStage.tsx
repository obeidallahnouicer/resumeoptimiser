import { motion } from 'motion/react';
import { useState, useEffect, useRef } from 'react';
import { ArrowRight, Loader2, AlertCircle, FileDiff } from 'lucide-react';
import { usePipeline } from '../../context/PipelineContext';
import { rewriteMarkdown, computeMarkdownDiff, ApiError } from '../../api';

interface RewriteStageProps { onComplete: () => void; }

// ---------------------------------------------------------------------------
// Diff line renderer
// ---------------------------------------------------------------------------

function DiffLine({ line }: { line: string }) {
  if (line.startsWith('+++') || line.startsWith('---')) {
    return (
      <div className="text-xs font-mono text-text-secondary opacity-50 px-2 py-0.5">{line}</div>
    );
  }
  if (line.startsWith('@@')) {
    return (
      <div className="text-xs font-mono text-text-secondary bg-bg-primary px-2 py-0.5 rounded">{line}</div>
    );
  }
  if (line.startsWith('+')) {
    return (
      <div className="font-mono text-xs bg-green-950/40 text-green-400 px-2 py-0.5 rounded-sm whitespace-pre-wrap">
        {line}
      </div>
    );
  }
  if (line.startsWith('-')) {
    return (
      <div className="font-mono text-xs bg-red-950/40 text-red-400 px-2 py-0.5 rounded-sm whitespace-pre-wrap">
        {line}
      </div>
    );
  }
  return (
    <div className="font-mono text-xs text-text-secondary px-2 py-0.5 whitespace-pre-wrap opacity-70">{line}</div>
  );
}

// ---------------------------------------------------------------------------
// Main stage component
// ---------------------------------------------------------------------------

export function RewriteStage({ onComplete }: RewriteStageProps) {
  const {
    originalMarkdown,
    improvedMarkdown,
    markdownDiff,
    structuredJob,
    explanationReport,
    setImprovedMarkdown,
    setMarkdownDiff,
    setError,
  } = usePipeline();

  const [loading, setLoading] = useState(!improvedMarkdown);
  const [errorMsg, setErrorMsg] = useState('');
  const [activeTab, setActiveTab] = useState<'diff' | 'original' | 'improved'>('diff');
  const calledRef = useRef(false);

  useEffect(() => {
    if (improvedMarkdown && markdownDiff) { setLoading(false); return; }
    if (!originalMarkdown) {
      setErrorMsg('Original Markdown not available. Please re-run the parse stage.');
      setLoading(false);
      return;
    }
    if (calledRef.current) return;
    calledRef.current = true;

    (async () => {
      try {
        // Build gap analysis string from the explanation report
        const gapAnalysis = explanationReport
          ? explanationReport.mismatches.map(m => `[${m.field}] ${m.explanation}`).join('\n')
          : '';

        // Step B: Rewrite markdown (wording only – structure preserved)
        const rewriteResult = await rewriteMarkdown({
          original_markdown: originalMarkdown,
          job_title: structuredJob?.title ?? '',
          job_description: structuredJob?.raw_text ?? '',
          gap_analysis: gapAnalysis,
        });
        setImprovedMarkdown(rewriteResult.improved_markdown);

        // Step C: Compute diff
        const diffResult = await computeMarkdownDiff({
          original_markdown: originalMarkdown,
          improved_markdown: rewriteResult.improved_markdown,
        });
        setMarkdownDiff(diffResult);
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : 'Rewrite failed.';
        setErrorMsg(msg);
        setError(msg);
      } finally {
        setLoading(false);
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ------------------------------------------------------------------
  // Loading / error states
  // ------------------------------------------------------------------

  if (loading) return (
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="w-10 h-10 text-accent animate-spin" />
      <span className="text-text-secondary font-mono text-sm">Improving wording (structure preserved)…</span>
    </div>
  );

  if (errorMsg) return (
    <div className="flex flex-col items-center gap-3 text-error">
      <AlertCircle className="w-8 h-8" />
      <span className="text-sm">{errorMsg}</span>
    </div>
  );

  const diffLines = markdownDiff?.diff_lines ?? [];
  const changeCount = markdownDiff?.change_count ?? 0;

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------

  return (
    <motion.div className="w-full h-full flex flex-col" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-text-primary">Content Improvement</h2>
          <p className="text-xs text-text-secondary mt-1 font-mono">
            Structure preserved · {changeCount} line(s) changed · Original always recoverable
          </p>
        </div>
        <div className="flex items-center gap-1 text-xs text-green-400 font-mono bg-green-950/30 px-3 py-1.5 rounded-full border border-green-800/40">
          <FileDiff className="w-3.5 h-3.5" />
          <span>{changeCount} changes</span>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-2 mb-4">
        {(['diff', 'original', 'improved'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors ${
              activeTab === tab
                ? 'bg-accent text-bg-primary'
                : 'bg-bg-card text-text-secondary hover:text-text-primary border border-border'
            }`}
          >
            {tab === 'diff' ? '± Diff' : tab === 'original' ? '📄 Original' : '✨ Improved'}
          </button>
        ))}
      </div>

      {/* Content panel */}
      <div className="flex-1 bg-bg-card border border-border rounded-xl overflow-y-auto p-4 min-h-[380px]">
        {activeTab === 'diff' && (
          diffLines.length === 0
            ? <p className="text-text-secondary text-sm font-mono text-center mt-8">No changes detected.</p>
            : <div className="space-y-0.5">
                {diffLines.map((line, i) => <DiffLine key={i} line={line} />)}
              </div>
        )}
        {activeTab === 'original' && (
          <pre className="font-mono text-xs text-text-secondary whitespace-pre-wrap leading-relaxed">
            {originalMarkdown}
          </pre>
        )}
        {activeTab === 'improved' && (
          <pre className="font-mono text-xs text-text-primary whitespace-pre-wrap leading-relaxed">
            {improvedMarkdown}
          </pre>
        )}
      </div>

      {/* Notice */}
      <div className="mt-3 px-4 py-2 rounded-lg bg-blue-950/20 border border-blue-800/30 text-xs text-blue-300 font-mono">
        ℹ️ The original CV is preserved unchanged. Only wording was improved. You can review every change above before proceeding.
      </div>

      {/* Continue button */}
      <div className="flex justify-end mt-6">
        <motion.button
          className="flex items-center gap-2 px-6 py-3 bg-accent text-bg-primary font-semibold rounded-xl hover:bg-white transition-colors"
          onClick={onComplete}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Finalize &amp; Compare <ArrowRight className="w-4 h-4" />
        </motion.button>
      </div>
    </motion.div>
  );
}
