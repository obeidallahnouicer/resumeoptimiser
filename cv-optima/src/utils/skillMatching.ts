/**
 * Skill matching utilities for the Skill Editor step.
 *
 * Provides deterministic, case-insensitive skill matching and presence computation.
 * No LLM calls – purely string normalization and comparison.
 */

/**
 * Normalize a skill string for comparison.
 *
 * Transforms to lowercase, trims whitespace, and removes most punctuation.
 * Preserves word boundaries (e.g. "C++" becomes "c", "C#" becomes "c").
 */
export function normalizeSkill(skill: string): string {
  return (
    skill
      .toLowerCase()
      .trim()
      // Remove common punctuation while preserving structure
      .replaceAll(/[^\w\s-]/g, '')
      .trim()
  );
}

/**
 * Result of skill presence matching.
 */
export interface SkillPresence {
  skill: string;
  present: boolean;
  normalized: string;
}

/**
 * Compute skill presence for all job-required skills against CV skills.
 *
 * Returns an array of SkillPresence objects, one per job skill.
 * Matching is case-insensitive and punctuation-agnostic.
 *
 * @param cvSkills - Array of skills extracted from the CV (hard + soft combined)
 * @param jobSkills - Array of skills required by the job
 * @returns Array of skill presence objects with original skill name and presence flag
 */
export function computeSkillPresence(
  cvSkills: string[],
  jobSkills: string[],
): SkillPresence[] {
  const normalizedCvSkills = new Set(cvSkills.map(normalizeSkill));

  return jobSkills.map((skill) => ({
    skill,
    normalized: normalizeSkill(skill),
    present: normalizedCvSkills.has(normalizeSkill(skill)),
  }));
}

/**
 * Add a skill to the CV skill list, preventing duplicates.
 *
 * If the skill (normalized) already exists in the list, does nothing.
 * Otherwise appends the skill to the array.
 *
 * @param cvSkills - Current list of CV skills
 * @param newSkill - Skill to add
 * @returns Updated array (or same reference if duplicate)
 */
export function addSkillToCV(cvSkills: string[], newSkill: string): string[] {
  const normalized = normalizeSkill(newSkill);
  const normalizedSet = new Set(cvSkills.map(normalizeSkill));

  if (normalizedSet.has(normalized)) {
    // Already present – don't add duplicate
    return cvSkills;
  }

  // Add the skill with original casing preserved
  return [...cvSkills, newSkill];
}
