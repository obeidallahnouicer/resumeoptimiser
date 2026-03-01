import { motion } from 'motion/react';
import { InsightCard } from '../ui/InsightCard';
import { Loader2, AlertCircle } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { usePipeline } from '../../context/PipelineContext';
import { explainMismatches, ApiError } from '../../api';

interface ExplainStageProps { onComplete: () => void; }

export function ExplainStage({ onComplete }: ExplainStageProps) {
  const { structuredCV, structuredJob, similarityScore, explanationReport, setExplanationReport, setError } = usePipeline();
  const [loading, setLoading] = useState(!explanationReport);
  const [errorMsg, setErrorMsg] = useState('');
  const calledRef = useRef(false);

  useEffect(() => {
    if (explanationReport) { setLoading(false); return; }
    if (!structuredCV || !structuredJob || !similarityScore) {
      setErrorMsg('Missing pipeline data.'); setLoading(false); return;
    }
    if (calledRef.current) return;
    calledRef.current = true;
    (async () => {
      try {
        const report = await explainMismatches({ cv: structuredCV, job: structuredJob, score: similarityScore });
        setExplanationReport(report);
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : 'Explanation failed.';
        setErrorMsg(msg); setError(msg);
      } finally { setLoading(false); }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) return (
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="w-10 h-10 text-accent animate-spin" />
      <span className="text-text-secondary font-mono text-sm">Analysing gaps with AI…</span>
    </div>
  );

  if (errorMsg) return (
    <div className="flex flex-col items-center gap-3 text-error">
      <AlertCircle className="w-8 h-8" /><span className="text-sm">{errorMsg}</span>
    </div>
  );

  const mismatches = explanationReport?.mismatches ?? [];
  const severityMap = (idx: number): 'high' | 'medium' | 'low' =>
    idx === 0 ? 'high' : idx <= 2 ? 'medium' : 'low';

  return (
    <motion.div className="w-full max-w-3xl mx-auto" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-semibold text-text-primary mb-2">Optimization Insights</h2>
        <p className="text-text-secondary">{explanationReport?.summary || `Found ${mismatches.length} areas to improve.`}</p>
      </div>
      <div className="space-y-4">
        {mismatches.map((m, idx) => (
          <InsightCard key={idx} title={m.field} description={m.explanation} severity={severityMap(idx)} index={idx} />
        ))}
      </div>
      <div className="flex justify-center mt-10">
        <motion.button
          className="px-8 py-3 bg-text-primary text-bg-primary font-semibold rounded-xl hover:bg-white transition-colors"
          onClick={onComplete} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
          Generate Optimized Version
        </motion.button>
      </div>
    </motion.div>
  );
}
