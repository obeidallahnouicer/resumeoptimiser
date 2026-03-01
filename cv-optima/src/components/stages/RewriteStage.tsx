import { motion } from 'motion/react';
import { useState, useEffect, useRef } from 'react';
import { ToggleLeft, ToggleRight, ArrowRight, Loader2, AlertCircle } from 'lucide-react';
import { usePipeline } from '../../context/PipelineContext';
import { rewriteCV, ApiError } from '../../api';

interface RewriteStageProps { onComplete: () => void; }

export function RewriteStage({ onComplete }: RewriteStageProps) {
  const { structuredCV, structuredJob, explanationReport, optimizedCV, setOptimizedCV, setError } = usePipeline();
  const [loading, setLoading] = useState(!optimizedCV);
  const [errorMsg, setErrorMsg] = useState('');
  const [showDiff, setShowDiff] = useState(false);
  const calledRef = useRef(false);

  useEffect(() => {
    if (optimizedCV) { setLoading(false); return; }
    if (!structuredCV || !structuredJob || !explanationReport) {
      setErrorMsg('Missing pipeline data.'); setLoading(false); return;
    }
    if (calledRef.current) return;
    calledRef.current = true;
    (async () => {
      try {
        const result = await rewriteCV({ cv: structuredCV, job: structuredJob, explanation: explanationReport });
        setOptimizedCV(result);
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : 'Rewrite failed.';
        setErrorMsg(msg); setError(msg);
      } finally { setLoading(false); }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) return (
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="w-10 h-10 text-accent animate-spin" />
      <span className="text-text-secondary font-mono text-sm">Rewriting CV sections…</span>
    </div>
  );

  if (errorMsg) return (
    <div className="flex flex-col items-center gap-3 text-error">
      <AlertCircle className="w-8 h-8" /><span className="text-sm">{errorMsg}</span>
    </div>
  );

  const origText = (structuredCV?.sections ?? []).map(s => `[${s.section_type.toUpperCase()}]\n${s.raw_text}`).join('\n\n');
  const optText = (optimizedCV?.sections ?? []).map(s => `[${s.section_type.toUpperCase()}]\n${s.raw_text}`).join('\n\n');
  const changes = optimizedCV?.changes_summary ?? [];

  return (
    <motion.div className="w-full h-full flex flex-col" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-text-primary">Content Optimization</h2>
        <button onClick={() => setShowDiff(!showDiff)}
          className="flex items-center gap-2 text-sm font-medium text-text-secondary hover:text-accent transition-colors">
          {showDiff ? <ToggleRight className="w-6 h-6 text-accent" /> : <ToggleLeft className="w-6 h-6" />}
          Show Changes
        </button>
      </div>

      <div className="grid grid-cols-2 gap-8" style={{ minHeight: 420 }}>
        <div className="flex flex-col gap-2">
          <span className="text-xs font-mono uppercase text-text-secondary tracking-wider">Original</span>
          <div className="flex-1 bg-bg-card border border-border rounded-xl p-6 font-mono text-sm text-text-secondary overflow-y-auto leading-relaxed whitespace-pre-wrap">
            {origText}
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-xs font-mono uppercase text-accent tracking-wider">Optimized by AI</span>
          <div className="flex-1 bg-bg-card border border-accent/30 rounded-xl p-6 font-mono text-sm text-text-primary overflow-y-auto leading-relaxed whitespace-pre-wrap relative">
            {showDiff
              ? changes.map((c, i) => (
                  <span key={i} className="block bg-success/20 text-success px-1 rounded mb-1">+ {c}</span>
                ))
              : optText}
            <div className="absolute top-4 right-4">
              <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end mt-8">
        <motion.button
          className="flex items-center gap-2 px-6 py-3 bg-accent text-bg-primary font-semibold rounded-xl hover:bg-white transition-colors"
          onClick={onComplete} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
          Finalize & Compare <ArrowRight className="w-4 h-4" />
        </motion.button>
      </div>
    </motion.div>
  );
}
