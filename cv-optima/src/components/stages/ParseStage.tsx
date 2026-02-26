import { motion } from 'motion/react';
import { CheckCircle2, Briefcase, GraduationCap, Code2, Loader2, AlertCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { usePipeline } from '../../context/PipelineContext';
import { parseCv, normalizeJob, ApiError } from '../../api';

interface ParseStageProps { onComplete: () => void; }

const SECTION_ICONS: Record<string, React.ElementType> = {
  experience: Briefcase, education: GraduationCap, skills: Code2,
};

export function ParseStage({ onComplete }: ParseStageProps) {
  const { cvText, jobText, structuredCV, structuredJob, setStructuredCV, setStructuredJob, setError } = usePipeline();
  const [loading, setLoading] = useState(!structuredCV);
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (structuredCV && structuredJob) { setLoading(false); return; }
    (async () => {
      try {
        const [cv, job] = await Promise.all([parseCv(cvText), normalizeJob(jobText)]);
        setStructuredCV(cv); setStructuredJob(job);
      } catch (err) {
        const msg = err instanceof ApiError ? err.message : 'Parsing failed.';
        setErrorMsg(msg); setError(msg);
      } finally { setLoading(false); }
    })();
  }, []); // eslint-disable-line

  if (loading) return (
    <div className="flex flex-col items-center gap-4">
      <Loader2 className="w-10 h-10 text-accent animate-spin" />
      <span className="text-text-secondary font-mono text-sm">Parsing CV &amp; Job Description…</span>
    </div>
  );

  if (errorMsg) return (
    <div className="flex flex-col items-center gap-3 text-error">
      <AlertCircle className="w-8 h-8" /><span className="text-sm">{errorMsg}</span>
    </div>
  );

  const sections = structuredCV?.sections ?? [];
  const skillsSection = sections.find(s => s.section_type === 'skills');
  const expSection = sections.find(s => s.section_type === 'experience');

  return (
    <motion.div className="w-full grid grid-cols-1 md:grid-cols-2 gap-8" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="space-y-6">
        <h3 className="text-xl font-medium text-text-primary flex items-center gap-2">
          <span className="w-1 h-6 bg-accent rounded-full" />Detected Structure
        </h3>
        <div className="space-y-4">
          {sections.map((section, idx) => {
            const Icon = SECTION_ICONS[section.section_type] ?? Briefcase;
            return (
              <motion.div key={section.section_type}
                className="bg-bg-card border border-border rounded-xl p-4 flex items-center justify-between"
                initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: idx * 0.1 }}>
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-bg-primary flex items-center justify-center text-text-secondary">
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-text-primary capitalize">{section.section_type}</div>
                    <div className="text-xs text-text-secondary">{section.items.length} items</div>
                  </div>
                </div>
                <CheckCircle2 className="w-5 h-5 text-success" />
              </motion.div>
            );
          })}
        </div>
      </div>
      <div className="space-y-6">
        <h3 className="text-xl font-medium text-text-primary flex items-center gap-2">
          <span className="w-1 h-6 bg-purple-500 rounded-full" />Signal Extraction
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <motion.div className="bg-bg-card border border-border rounded-2xl p-6 flex flex-col items-center text-center"
            initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.3 }}>
            <span className="text-4xl font-bold text-text-primary mb-1">{expSection?.items.length ?? 0}</span>
            <span className="text-xs text-text-secondary uppercase tracking-wider">Exp. Items</span>
          </motion.div>
          <motion.div className="bg-bg-card border border-border rounded-2xl p-6 flex flex-col items-center text-center"
            initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.4 }}>
            <span className="text-4xl font-bold text-accent mb-1">{skillsSection?.items.length ?? structuredJob?.required_skills.length ?? 0}</span>
            <span className="text-xs text-text-secondary uppercase tracking-wider">Skills</span>
          </motion.div>
        </div>
        <motion.div className="bg-bg-card border border-border rounded-2xl p-6"
          initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.5 }}>
          <div className="flex justify-between items-center mb-4">
            <span className="text-sm font-medium text-text-secondary">Job Title</span>
            <span className="px-2 py-1 rounded bg-accent/10 text-accent text-xs font-mono">PARSED</span>
          </div>
          <div className="text-xl font-semibold text-text-primary">{structuredJob?.title ?? '–'}</div>
          <div className="mt-2 text-sm text-text-secondary capitalize">{structuredJob?.employment_type.replace('_',' ') ?? ''}</div>
        </motion.div>
        <motion.button className="w-full px-6 py-3 bg-accent text-bg-primary font-semibold rounded-xl hover:bg-white transition-colors"
          onClick={onComplete} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}>
          Compute Match Score
        </motion.button>
      </div>
    </motion.div>
  );
}
