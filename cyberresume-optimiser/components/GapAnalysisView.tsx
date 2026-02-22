import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, TrendingDown, Lightbulb } from 'lucide-react';
import { GapAnalysisItem } from '../types';

interface GapAnalysisViewProps {
  gaps: GapAnalysisItem[];
}

export const GapAnalysisView: React.FC<GapAnalysisViewProps> = ({ gaps }) => {
  const getSeverityColor = (severity: string) => {
    const colors: Record<string, { bg: string; text: string; border: string }> = {
      critical: {
        bg: 'bg-red-900/20',
        text: 'text-red-400',
        border: 'border-red-500/30'
      },
      high: {
        bg: 'bg-orange-900/20',
        text: 'text-orange-400',
        border: 'border-orange-500/30'
      },
      moderate: {
        bg: 'bg-yellow-900/20',
        text: 'text-yellow-400',
        border: 'border-yellow-500/30'
      },
      low: {
        bg: 'bg-blue-900/20',
        text: 'text-blue-400',
        border: 'border-blue-500/30'
      }
    };
    return colors[severity] || colors.low;
  };

  const getGapTypeIcon = (gapType: string) => {
    const icons: Record<string, React.ReactNode> = {
      skill_gap: '⚙️',
      wording_gap: '📝',
      structural_gap: '🏗️',
      experience_gap: '⏱️'
    };
    return icons[gapType] || '•';
  };

  const getGapTypeLabel = (gapType: string) => {
    const labels: Record<string, string> = {
      skill_gap: 'Skill Gap',
      wording_gap: 'Wording Gap',
      structural_gap: 'Structural Gap',
      experience_gap: 'Experience Gap'
    };
    return labels[gapType] || gapType;
  };

  const criticalGaps = gaps.filter((g) => g.severity === 'critical');
  const highGaps = gaps.filter((g) => g.severity === 'high');
  const moderateGaps = gaps.filter((g) => g.severity === 'moderate');

  return (
    <motion.div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {criticalGaps.length > 0 && (
          <motion.div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
            <p className="text-xs text-red-400 font-semibold uppercase">Critical Gaps</p>
            <p className="text-2xl font-bold text-red-300">{criticalGaps.length}</p>
          </motion.div>
        )}
        {highGaps.length > 0 && (
          <motion.div className="bg-orange-900/20 border border-orange-500/30 rounded-lg p-3">
            <p className="text-xs text-orange-400 font-semibold uppercase">High Priority</p>
            <p className="text-2xl font-bold text-orange-300">{highGaps.length}</p>
          </motion.div>
        )}
        {moderateGaps.length > 0 && (
          <motion.div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3">
            <p className="text-xs text-yellow-400 font-semibold uppercase">Moderate</p>
            <p className="text-2xl font-bold text-yellow-300">{moderateGaps.length}</p>
          </motion.div>
        )}
      </div>

      {/* Gap List */}
      <motion.div className="bg-gray-900/50 border border-cyan-500/20 rounded-lg p-6 backdrop-blur">
        <h3 className="text-lg font-semibold text-cyan-300 mb-4 flex items-center gap-2">
          <AlertCircle size={20} />
          Gap Analysis
        </h3>

        <div className="space-y-3">
          {gaps.map((gap, index) => {
            const colors = getSeverityColor(gap.severity);
            return (
              <motion.div
                key={`${gap.gap_id}-${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`${colors.bg} border ${colors.border} rounded-lg p-4 space-y-2`}
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1">
                    <span className="text-lg mt-1">
                      {getGapTypeIcon(gap.gap_type)}
                    </span>
                    <div className="flex-1">
                      <h4 className={`font-semibold ${colors.text}`}>
                        {gap.requirement}
                      </h4>
                      <p className="text-xs text-gray-400 mt-1">
                        {getGapTypeLabel(gap.gap_type)} •{' '}
                        {Math.round(gap.similarity * 100)}% similarity to CV
                      </p>
                    </div>
                  </div>
                  <span
                    className={`text-xs font-bold px-2 py-1 rounded uppercase tracking-wider ${colors.text}`}
                  >
                    {gap.severity}
                  </span>
                </div>

                {/* Closest Match */}
                {gap.closest_match && (
                  <div className="flex items-start gap-2 text-sm text-gray-300 ml-8">
                    <TrendingDown size={14} className="flex-shrink-0 mt-0.5 text-blue-400" />
                    <div>
                      <p className="text-gray-500">Your experience:</p>
                      <p className="text-blue-300">{gap.closest_match}</p>
                    </div>
                  </div>
                )}

                {/* Suggested Improvement */}
                {gap.suggested_improvement && (
                  <div className="flex items-start gap-2 text-sm text-gray-300 ml-8">
                    <Lightbulb size={14} className="flex-shrink-0 mt-0.5 text-yellow-400" />
                    <div>
                      <p className="text-gray-500">Suggestion:</p>
                      <p className="text-yellow-300">{gap.suggested_improvement}</p>
                    </div>
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </motion.div>
  );
};
