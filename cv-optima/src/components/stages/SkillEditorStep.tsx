import { motion } from 'motion/react';
import { Plus, CheckCircle2, AlertCircle, Code2, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { usePipeline } from '../../context/PipelineContext';
import { computeSkillPresence, addSkillToCV } from '../../utils/skillMatching';
import type { SkillPresence } from '../../utils/skillMatching';

interface SkillEditorStepProps {
  readonly onComplete: () => void;
}

/**
 * SkillEditorStep – manual validation and correction of skill extraction.
 *
 * Displays job-required skills and flags which are present in the CV.
 * Allows users to add missing skills before the matching stage runs.
 *
 * This step is purely deterministic – no LLM calls.
 */
export function SkillEditorStep(props: SkillEditorStepProps) {
  const { onComplete } = props;
  const {
    structuredCV,
    structuredJob,
    editedHardSkills,
    setEditedHardSkills,
    setError,
  } = usePipeline();

  const [skillPresence, setSkillPresence] = useState<SkillPresence[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');

  // Initialize on mount – compute skill presence
  useEffect(() => {
    try {
      if (!structuredCV || !structuredJob) {
        throw new Error('Missing CV or Job data.');
      }

      // Use edited hard skills if available, otherwise use parsed hard skills
      const cvHardSkills = editedHardSkills ?? structuredCV.hard_skills ?? [];
      const jobRequiredSkills = structuredJob.required_skills?.map((rs) => rs.skill) ?? [];

      // Compute presence
      const presence = computeSkillPresence(cvHardSkills, jobRequiredSkills);
      setSkillPresence(presence);

      // Initialize edited skills if not already done
      if (editedHardSkills === null) {
        setEditedHardSkills(cvHardSkills);
      }

      setLoading(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load skill editor.';
      setErrorMsg(msg);
      setError(msg);
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle adding a skill
  const handleAddSkill = (skill: string) => {
    if (!editedHardSkills) return;

    const updated = addSkillToCV(editedHardSkills, skill);
    setEditedHardSkills(updated);

    // Recompute presence
    const jobRequiredSkills = structuredJob?.required_skills?.map((rs) => rs.skill) ?? [];
    const presence = computeSkillPresence(updated, jobRequiredSkills);
    setSkillPresence(presence);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="w-10 h-10 text-accent animate-spin" />
        <span className="text-text-secondary font-mono text-sm">Analyzing required skills…</span>
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div className="flex flex-col items-center gap-3 text-error">
        <AlertCircle className="w-8 h-8" />
        <span className="text-sm">{errorMsg}</span>
      </div>
    );
  }

  const presentCount = skillPresence.filter((s) => s.present).length;
  const missingCount = skillPresence.filter((s) => !s.present).length;

  return (
    <motion.div
      className="w-full max-w-4xl flex flex-col gap-10"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-bg-primary flex items-center justify-center text-accent">
            <Code2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xl font-medium text-text-primary">Skill Validation</h3>
            <p className="text-sm text-text-secondary">
              Review and add any skills from the job description that may be missing from your CV
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          <motion.div
            className="flex flex-col items-center p-4 bg-bg-card border border-border rounded-xl"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            <span className="text-3xl font-bold text-success">{presentCount}</span>
            <span className="text-xs text-text-secondary uppercase tracking-wider mt-1">
              Present in CV
            </span>
          </motion.div>

          <motion.div
            className="flex flex-col items-center p-4 bg-bg-card border border-border rounded-xl"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.15 }}
          >
            <span className="text-3xl font-bold text-error">{missingCount}</span>
            <span className="text-xs text-text-secondary uppercase tracking-wider mt-1">
              Missing
            </span>
          </motion.div>
        </div>
      </div>

      {/* Skill List */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-text-secondary uppercase tracking-wider border-b border-border pb-2">
          Job Required Skills
        </h4>

        <div className="grid gap-3">
          {skillPresence.map((skillItem, idx) => (
            <motion.div
              key={`${skillItem.normalized}-${idx}`}
              className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                skillItem.present
                  ? 'bg-bg-card border-border hover:border-success/50'
                  : 'bg-bg-card border-border hover:bg-bg-primary'
              }`}
              initial={{ x: -10, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.2 + idx * 0.04 }}
            >
              <div className="flex items-center gap-3 flex-1">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                    skillItem.present ? 'bg-success/20' : 'bg-error/20'
                  }`}
                >
                  {skillItem.present ? (
                    <CheckCircle2 className="w-4 h-4 text-success" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-error" />
                  )}
                </div>
                <span className="text-sm font-medium text-text-primary">{skillItem.skill}</span>
              </div>

              {skillItem.present ? (
                <span className="text-xs font-medium text-success px-3 py-1 rounded-full bg-success/10">
                  Present
                </span>
              ) : (
                <button
                  onClick={() => handleAddSkill(skillItem.skill)}
                  className="flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 hover:bg-accent/20 text-accent text-xs font-medium transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Add
                </button>
              )}
            </motion.div>
          ))}
        </div>
      </div>

      {/* Current CV Skills Display */}
      {editedHardSkills && editedHardSkills.length > 0 && (
        <div className="space-y-2 p-4 bg-bg-primary rounded-lg border border-border">
          <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider">
            Your Skills ({editedHardSkills.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {editedHardSkills.map((skill, idx) => (
              <motion.span
                key={`cv-skill-${skill}-${idx}`}
                className="inline-block px-3 py-1 rounded-full bg-accent/10 text-accent text-xs font-medium"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.3 + idx * 0.02 }}
              >
                {skill}
              </motion.span>
            ))}
          </div>
        </div>
      )}

      {/* Continue Button */}
      <motion.button
        onClick={onComplete}
        className="w-full px-6 py-3 rounded-lg bg-accent text-white font-medium hover:bg-accent/90 transition-colors"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        Continue to Matching
      </motion.button>
    </motion.div>
  );
}
