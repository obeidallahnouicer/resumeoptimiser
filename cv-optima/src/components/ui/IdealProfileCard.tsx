/**
 * IdealProfileCard.tsx
 *
 * Displays the ideal candidate profile for the target job.
 * Shows what the system is optimizing the CV toward.
 *
 * Components shown:
 * - Title (role summary)
 * - Core competencies
 * - Technical stack
 * - Preferred action verbs (optional)
 * - Impact patterns (optional)
 * - Domain language (optional)
 */

import React from 'react';
import { IdealProfile } from '../../types/pipeline';

interface IdealProfileCardProps {
  profile: IdealProfile;
  /**
   * Show additional sections like verbs and patterns.
   * Default: false (compact mode shows only core info)
   */
  expanded?: boolean;
}

export const IdealProfileCard: React.FC<IdealProfileCardProps> = ({
  profile,
  expanded = false,
}) => {
  if (!profile) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
      {/* Title */}
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Ideal Candidate Profile
      </h3>

      {/* Role Summary */}
      {profile.role_summary && (
        <div className="mb-5 pb-5 border-b border-gray-100">
          <p className="text-gray-700 text-sm leading-relaxed">
            {profile.role_summary}
          </p>
        </div>
      )}

      {/* Core Competencies */}
      {profile.core_competencies && profile.core_competencies.length > 0 && (
        <div className="mb-5">
          <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
            Core Competencies
          </h4>
          <div className="flex flex-wrap gap-2">
            {profile.core_competencies.map((competency) => (
              <span
                key={competency}
                className="inline-block px-3 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full border border-blue-200"
              >
                {competency}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Technical Stack */}
      {profile.technical_stack && profile.technical_stack.length > 0 && (
        <div className="mb-5">
          <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
            Tech Stack
          </h4>
          <div className="flex flex-wrap gap-1">
            {profile.technical_stack.map((tech) => (
              <span
                key={tech}
                className="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs font-mono border border-gray-300 rounded"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Expanded Sections */}
      {expanded && (
        <>
          {/* Preferred Action Verbs */}
          {profile.preferred_action_verbs && profile.preferred_action_verbs.length > 0 && (
            <div className="mb-5 pt-5 border-t border-gray-100">
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                Preferred Action Verbs
              </h4>
              <p className="text-sm text-gray-700">
                {profile.preferred_action_verbs.join(', ')}
              </p>
            </div>
          )}

          {/* Impact Patterns */}
          {profile.impact_patterns && profile.impact_patterns.length > 0 && (
            <div className="mb-5 pt-5 border-t border-gray-100">
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                Impact Patterns
              </h4>
              <ul className="list-disc list-inside space-y-1">
                {profile.impact_patterns.map((pattern) => (
                  <li key={pattern} className="text-sm text-gray-700">
                    {pattern}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Domain Language */}
          {profile.domain_language && profile.domain_language.length > 0 && (
            <div className="pt-5 border-t border-gray-100">
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                Domain Language
              </h4>
              <p className="text-sm text-gray-700">
                {profile.domain_language.join(', ')}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default IdealProfileCard;
