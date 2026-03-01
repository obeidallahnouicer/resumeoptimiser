import { motion } from 'motion/react';
import { ArrowUpRight, Download, Loader2, AlertCircle } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { usePipeline } from '../../context/PipelineContext';
import { compareResults, ApiError } from '../../api';
import { exportOptimizedCvToPdf } from '../../lib/exportPdf';

interface CompareStageProps { readonly onReset?: () => void; }

export function CompareStage({ onReset }: CompareStageProps) {
  const {
    structuredCV, structuredJob, similarityScore, explanationReport, optimizedCV,
    comparisonReport, setComparisonReport, setError,
  } = usePipeline();
  const [loading, setLoading] = useState(!comparisonReport);
  const [errorMsg, setErrorMsg] = useState('');
  const calledRef = useRef(false);

  useEffect(() => {
    if (comparisonReport) { setLoading(false); return; }
    if (!structuredCV || !structuredJob || !similarityScore || !explanationReport || !optimizedCV) {
      setErrorMsg('Missing pipeline data.'); setLoading(false); return;
    }
    if (calledRef.current) return;
    calledRef.current = true;
    const optimizedAsStructured = { ...structuredCV, sections: optimizedCV.sections, contact: optimizedCV.contact };
    (async () => {
      try {
        const report = await compareResults({
          original_cv: structuredCV,
          optimized_cv: optimizedAsStructured,
          job: structuredJob,
          original_score: similarityScore,
          explanation: explanationReport,
          optimized_cv_schema: optimizedCV,
        });
        setComparisonReport(report);
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : 'Comparison failed.';
        setErrorMsg(msg); setError(msg);
      } finally { setLoading(false); }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) return (
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="w-10 h-10 text-accent animate-spin" />
      <span className="text-text-secondary font-mono text-sm">Computing final scores…</span>
    </div>
  );

  if (errorMsg) return (
    <div className="flex flex-col items-center gap-3 text-error">
      <AlertCircle className="w-8 h-8" /><span className="text-sm">{errorMsg}</span>
    </div>
  );

  const before = comparisonReport?.improved_score.before.overall ?? 0;
  const after = comparisonReport?.improved_score.after.overall ?? 0;
  const delta = comparisonReport?.improved_score.delta ?? 0;
  const changes = comparisonReport?.optimized_cv.changes_summary ?? [];

  const handleDownloadPdf = () => {
    if (!comparisonReport) return;
    const cv = comparisonReport.optimized_cv;
    const name = cv.contact?.name?.trim().replaceAll(' ', '-') || 'candidate';
    exportOptimizedCvToPdf(cv, `${name}-optimized-cv.pdf`);
  };

  const metrics = [
    { label: 'Match Before', value: `${Math.round(before * 100)}%`, diff: null },
    { label: 'Match After', value: `${Math.round(after * 100)}%`, diff: null },
    { label: 'Improvement', value: `+${Math.round(delta * 100)}%`, diff: delta },
    { label: 'Gaps Fixed', value: String(comparisonReport?.explanation.mismatches.length ?? 0), diff: null },
  ];

  return (
    <motion.div className="w-full max-w-4xl mx-auto" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-text-primary mb-2">Optimization Complete</h2>
        <p className="text-text-secondary">{comparisonReport?.narrative || 'Your CV has been optimized.'}</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {metrics.map((m, idx) => (
          <motion.div key={m.label}
            className="bg-bg-card border border-border rounded-2xl p-6 relative overflow-hidden"
            initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: idx * 0.1 }}>
            <div className="text-xs text-text-secondary uppercase tracking-wider mb-4">{m.label}</div>
            <div className="flex items-end justify-between">
              <div className={`text-3xl font-bold ${m.diff && m.diff > 0 ? 'text-success' : 'text-text-primary'}`}>
                {m.value}
              </div>
              {m.diff !== null && m.diff > 0 && (
                <div className="flex items-center text-success text-sm font-medium bg-success/10 px-2 py-1 rounded">
                  <ArrowUpRight className="w-3 h-3" />
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {changes.length > 0 && (
        <div className="mb-10 bg-bg-card border border-border rounded-2xl p-6">
          <h3 className="text-sm font-medium text-text-secondary uppercase tracking-wider mb-4">Changes Made</h3>
          <ul className="space-y-2">
            {changes.map((c) => (
              <li key={c} className="flex items-start gap-2 text-sm text-text-primary">
                <span className="text-success mt-0.5">✓</span>{c}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex justify-center gap-4">
        <motion.button
          onClick={handleDownloadPdf}
          className="flex items-center gap-2 px-8 py-4 bg-accent text-bg-primary font-bold rounded-xl hover:bg-white transition-colors shadow-[0_0_30px_var(--color-accent-dim)]"
          whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
          <Download className="w-5 h-5" />Download PDF
        </motion.button>
        {onReset && (
          <motion.button
            className="flex items-center gap-2 px-8 py-4 text-text-secondary hover:text-text-primary transition-colors"
            onClick={onReset} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            Start Over
          </motion.button>
        )}
      </div>
    </motion.div>
  );
}
