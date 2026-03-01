import { motion } from 'motion/react';
import { HeroScore } from '../ui/HeroScore';
import { Check, X, Loader2, AlertCircle } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { usePipeline } from '../../context/PipelineContext';
import { matchCvToJob, ApiError } from '../../api';

interface MatchStageProps { onComplete: () => void; }

export function MatchStage({ onComplete }: MatchStageProps) {
  const { structuredCV, structuredJob, similarityScore, setSimilarityScore, setError } = usePipeline();
  const [loading, setLoading] = useState(!similarityScore);
  const [errorMsg, setErrorMsg] = useState('');
  const calledRef = useRef(false);

  useEffect(() => {
    if (similarityScore) { setLoading(false); return; }
    if (!structuredCV || !structuredJob) { setErrorMsg('Missing CV or Job data.'); setLoading(false); return; }
    if (calledRef.current) return;
    calledRef.current = true;
    (async () => {
      try {
        const score = await matchCvToJob({ cv: structuredCV, job: structuredJob });
        setSimilarityScore(score);
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : 'Matching failed.';
        setErrorMsg(msg); setError(msg);
      } finally { setLoading(false); }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
  const llm = similarityScore?.llm_analysis;
  const sectionMap = Object.fromEntries(
    (similarityScore?.section_scores ?? []).map(s => [s.section_type, s.score])
  );

  // Use LLM skill_details when available, else fall back to required_skills list
  const skillDetails = llm?.skill_details ?? [];
  const fallbackSkills = (structuredJob?.required_skills ?? []).slice(0, 8).map(r => ({
    skill: r.skill,
    found_in_cv: false,
    cv_evidence: '',
  }));
  const displaySkills = skillDetails.length > 0 ? skillDetails.slice(0, 10) : fallbackSkills;

  // LLM sub-scores for the 4-dimension breakdown
  const dimensions = llm
    ? [
        { label: 'Skills', value: llm.skills_match_score },
        { label: 'Experience', value: llm.experience_match_score },
        { label: 'Education', value: llm.education_match_score },
        { label: 'Languages', value: llm.languages_match_score },
      ]
    : Object.entries(sectionMap)
        .slice(0, 4)
        .map(([type, score]) => ({ label: type, value: score }));

  return (
    <motion.div className="w-full flex flex-col items-center gap-10" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>

      {/* Hero score + LLM sub-scores */}
      <div className="flex flex-col items-center gap-8 w-full max-w-3xl">
        <HeroScore score={scorePercent} label="Match Score" />
        <div className="grid grid-cols-4 gap-4 w-full">
          {dimensions.map((d, idx) => (
            <motion.div key={d.label}
              className="flex flex-col items-center p-4 bg-bg-card border border-border rounded-xl"
              initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.6 + idx * 0.1 }}>
              <span className="text-2xl font-bold text-accent">{Math.round(d.value * 100)}%</span>
              <span className="text-xs text-text-secondary uppercase tracking-wider mt-1 capitalize">{d.label}</span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Skill match table + strengths/gaps */}
      <div className="w-full max-w-4xl grid grid-cols-2 gap-8">
        {/* Left: per-skill found/missing from LLM */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-text-secondary uppercase tracking-wider mb-3 border-b border-border pb-2">
            Skill Analysis
          </h4>
          {displaySkills.map((s, idx) => (
            <motion.div key={s.skill}
              className="flex items-center justify-between p-3 rounded-lg hover:bg-bg-card transition-colors"
              initial={{ x: -10, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.9 + idx * 0.06 }}>
              <div className="flex flex-col min-w-0">
                <span className="text-text-primary text-sm truncate">{s.skill}</span>
                {s.cv_evidence && (
                  <span className="text-xs text-text-secondary truncate">{s.cv_evidence}</span>
                )}
              </div>
              {s.found_in_cv
                ? <Check className="w-4 h-4 text-success flex-shrink-0 ml-2" />
                : <X className="w-4 h-4 text-error flex-shrink-0 ml-2" />}
            </motion.div>
          ))}
        </div>

        {/* Right: strengths + gaps from LLM, or CV section scores fallback */}
        <div className="space-y-4">
          {llm ? (
            <>
              {llm.strengths.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-success uppercase tracking-wider mb-2 border-b border-border pb-2">
                    Strengths
                  </h4>
                  <ul className="space-y-2">
                    {llm.strengths.map((s) => (
                      <li key={s} className="flex items-start gap-2 text-sm text-text-primary">
                        <Check className="w-3 h-3 text-success mt-1 flex-shrink-0" />{s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {llm.gaps.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-error uppercase tracking-wider mb-2 border-b border-border pb-2">
                    Key Gaps
                  </h4>
                  <ul className="space-y-2">
                    {llm.gaps.map((g) => (
                      <li key={g} className="flex items-start gap-2 text-sm text-text-primary">
                        <X className="w-3 h-3 text-error mt-1 flex-shrink-0" />{g}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {llm.reasoning && (
                <div className="bg-bg-card border border-border rounded-xl p-4 mt-2">
                  <p className="text-xs text-text-secondary italic">{llm.reasoning}</p>
                </div>
              )}
            </>
          ) : (
            <>
              <h4 className="text-sm font-medium text-text-secondary uppercase tracking-wider mb-3 border-b border-border pb-2">
                CV Sections
              </h4>
              {(structuredCV?.sections ?? []).slice(0, 5).map((section) => (
                <motion.div key={section.section_type}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-bg-card transition-colors"
                  initial={{ x: 10, opacity: 0 }} animate={{ x: 0, opacity: 1 }}>
                  <span className="text-text-primary text-sm capitalize">{section.section_type}</span>
                  <span className="text-xs text-text-secondary bg-bg-primary px-2 py-1 rounded border border-border">
                    {Math.round((sectionMap[section.section_type] ?? 0) * 100)}%
                  </span>
                </motion.div>
              ))}
            </>
          )}
        </div>
      </div>

      <motion.button
        className="mt-4 px-8 py-3 bg-accent text-bg-primary font-semibold rounded-xl hover:bg-white transition-colors shadow-[0_0_20px_var(--color-accent-dim)]"
        onClick={onComplete} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
        Analyze Gaps
      </motion.button>
    </motion.div>
  );
}
