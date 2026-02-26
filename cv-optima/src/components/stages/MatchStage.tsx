import { motion } from 'motion/react';
import { HeroScore } from '../ui/HeroScore';
import { Check, X, Minus, Loader2, AlertCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { usePipeline } from '../../context/PipelineContext';
import { matchCvToJob, ApiError } from '../../api';

interface MatchStageProps { onComplete: () => void; }

export function MatchStage({ onComplete }: MatchStageProps) {
  const { structuredCV, structuredJob, similarityScore, setSimilarityScore, setError } = usePipeline();
  const [loading, setLoading] = useState(!similarityScore);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (similarityScore) { setLoading(false); return; }
    if (!structuredCV || !structuredJob) { setErrorMsg('Missing CV or Job data.'); setLoading(false); return; }
    (async () => {
      try {
        const score = await matchCvToJob({ cv: structuredCV, job: structuredJob });
        setSimilarityScore(score);
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : 'Matching failed.';
        setErrorMsg(msg); setError(msg);
      } finally { setLoading(false); }
    })();
  }, []); // eslint-disable-line

  if (loading) return (
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="w-10 h-10 text-accent animate-spin" />
      <span className="text-text-secondary font-mono text-sm">Computing semantic similarity…</span>
    </div>
  );

  if (errorMsg) return (
    <div className="flex flex-col items-center gap-3 text-error">
      <AlertCircle className="w-8 h-8" /><span className="text-sm">{errorMsg}</span>
    </div>
  );

  const scorePercent = Math.round((similarityScore?.overall ?? 0) * 100);
  const sectionMap = Object.fromEntries((similarityScore?.section_scores ?? []).map(s => [s.section_type, s.score]));
  const skills = structuredJob?.required_skills ?? [];

  return (
    <motion.div className="w-full flex flex-col items-center gap-12" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="flex flex-col items-center gap-8">
        <HeroScore score={scorePercent} label="Match Score" />
        <div className="grid grid-cols-3 gap-8 w-full max-w-2xl">
          {Object.entries(sectionMap).slice(0, 3).map(([type, score], idx) => (
            <motion.div key={type}
              className="flex flex-col items-center p-4 bg-bg-card border border-border rounded-xl"
              initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.8 + idx * 0.1 }}>
              <span className="text-2xl font-bold text-accent">{Math.round(score * 100)}%</span>
              <span className="text-xs text-text-secondary uppercase tracking-wider mt-1 capitalize">{type}</span>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="w-full max-w-4xl grid grid-cols-2 gap-8 mt-8">
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-text-secondary uppercase tracking-wider mb-4 border-b border-border pb-2">Job Requirements</h4>
          {skills.slice(0, 6).map((req, idx) => {
            const sectionScore = sectionMap['skills'] ?? 0;
            const status = sectionScore > 0.7 ? 'match' : sectionScore > 0.4 ? 'partial' : 'missing';
            return (
              <motion.div key={idx}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-bg-card transition-colors"
                initial={{ x: -10, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 1.2 + idx * 0.08 }}>
                <span className="text-text-primary text-sm">{req.skill}</span>
                {status === 'match' && <Check className="w-4 h-4 text-success" />}
                {status === 'partial' && <Minus className="w-4 h-4 text-yellow-500" />}
                {status === 'missing' && <X className="w-4 h-4 text-error" />}
              </motion.div>
            );
          })}
        </div>
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-text-secondary uppercase tracking-wider mb-4 border-b border-border pb-2">CV Signals</h4>
          {(structuredCV?.sections ?? []).slice(0, 5).map((section, idx) => (
            <motion.div key={idx}
              className="flex items-center justify-between p-3 rounded-lg hover:bg-bg-card transition-colors"
              initial={{ x: 10, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 1.2 + idx * 0.08 }}>
              <span className="text-text-primary text-sm capitalize">{section.section_type}</span>
              <span className="text-xs text-text-secondary bg-bg-primary px-2 py-1 rounded border border-border">
                {Math.round((sectionMap[section.section_type] ?? 0) * 100)}%
              </span>
            </motion.div>
          ))}
        </div>
      </div>

      <motion.button
        className="mt-8 px-8 py-3 bg-accent text-bg-primary font-semibold rounded-xl hover:bg-white transition-colors shadow-[0_0_20px_var(--color-accent-dim)]"
        onClick={onComplete} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
        Analyze Gaps
      </motion.button>
    </motion.div>
  );
}
