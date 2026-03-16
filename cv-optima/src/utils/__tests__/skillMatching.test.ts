/**
 * Unit tests for skill matching utilities.
 *
 * Tests the deterministic, LLM-free skill normalization and matching logic.
 */

import { describe, it, expect } from 'vitest';
import {
  normalizeSkill,
  computeSkillPresence,
  addSkillToCV,
} from '../skillMatching';

describe('skillMatching utilities', () => {
  describe('normalizeSkill', () => {
    it('should lowercase skill names', () => {
      expect(normalizeSkill('Python')).toBe('python');
      expect(normalizeSkill('JAVASCRIPT')).toBe('javascript');
    });

    it('should trim whitespace', () => {
      expect(normalizeSkill('  Python  ')).toBe('python');
      expect(normalizeSkill('\tDocker\n')).toBe('docker');
    });

    it('should remove punctuation and special characters', () => {
      expect(normalizeSkill('C++')).toContain('c');
      expect(normalizeSkill('C#')).toContain('c');
      expect(normalizeSkill('Node.js')).toBe('nodejs');
    });

    it('should handle complex skill names', () => {
      expect(normalizeSkill('AWS Lambda')).toBe('aws lambda');
      expect(normalizeSkill('Machine Learning')).toBe('machine learning');
    });

    it('should be idempotent', () => {
      const skill = 'Python';
      const once = normalizeSkill(skill);
      const twice = normalizeSkill(once);
      expect(once).toBe(twice);
    });
  });

  describe('computeSkillPresence', () => {
    it('should return array with same length as job skills', () => {
      const cvSkills = ['Python', 'Docker'];
      const jobSkills = ['Python', 'Kubernetes', 'AWS'];
      const result = computeSkillPresence(cvSkills, jobSkills);
      expect(result).toHaveLength(jobSkills.length);
    });

    it('should mark present skills correctly', () => {
      const cvSkills = ['Python', 'Docker'];
      const jobSkills = ['Python', 'Docker', 'Kubernetes'];
      const result = computeSkillPresence(cvSkills, jobSkills);

      expect(result[0]).toEqual({
        skill: 'Python',
        normalized: 'python',
        present: true,
      });
      expect(result[1]).toEqual({
        skill: 'Docker',
        normalized: 'docker',
        present: true,
      });
      expect(result[2]).toEqual({
        skill: 'Kubernetes',
        normalized: 'kubernetes',
        present: false,
      });
    });

    it('should be case-insensitive', () => {
      const cvSkills = ['python', 'DOCKER'];
      const jobSkills = ['Python', 'Docker', 'Kubernetes'];
      const result = computeSkillPresence(cvSkills, jobSkills);

      expect(result[0].present).toBe(true);
      expect(result[1].present).toBe(true);
    });

    it('should ignore punctuation differences', () => {
      const cvSkills = ['C++', 'C#', 'Node.js'];
      const jobSkills = ['C++', 'C#', 'Node.js'];
      const result = computeSkillPresence(cvSkills, jobSkills);

      // All should be "present" since normalized forms match
      result.forEach((r) => expect(r.present).toBe(true));
    });

    it('should handle empty CV skills', () => {
      const cvSkills: string[] = [];
      const jobSkills = ['Python', 'Docker'];
      const result = computeSkillPresence(cvSkills, jobSkills);

      expect(result.every((r) => !r.present)).toBe(true);
    });

    it('should handle empty job skills', () => {
      const cvSkills = ['Python', 'Docker'];
      const jobSkills: string[] = [];
      const result = computeSkillPresence(cvSkills, jobSkills);

      expect(result).toHaveLength(0);
    });
  });

  describe('addSkillToCV', () => {
    it('should add a new skill to the list', () => {
      const cvSkills = ['Python', 'Docker'];
      const result = addSkillToCV(cvSkills, 'Kubernetes');

      expect(result).toContain('Kubernetes');
      expect(result).toHaveLength(3);
    });

    it('should preserve original casing when adding', () => {
      const cvSkills = ['Python'];
      const result = addSkillToCV(cvSkills, 'Kubernetes');

      expect(result).toContain('Kubernetes');
    });

    it('should prevent adding duplicate skills (case-insensitive)', () => {
      const cvSkills = ['Python', 'Docker'];
      const result1 = addSkillToCV(cvSkills, 'python');

      expect(result1).toHaveLength(2);
      expect(result1).toEqual(cvSkills);
    });

    it('should prevent adding duplicate skills with different punctuation', () => {
      const cvSkills = ['Node.js'];
      const result = addSkillToCV(cvSkills, 'nodejs');

      expect(result).toHaveLength(1);
    });

    it('should return new array reference', () => {
      const cvSkills = ['Python'];
      const result = addSkillToCV(cvSkills, 'Docker');

      expect(result).not.toBe(cvSkills);
    });

    it('should return same array reference for duplicate', () => {
      const cvSkills = ['Python'];
      const result = addSkillToCV(cvSkills, 'python');

      expect(result).toBe(cvSkills);
    });

    it('should handle multiple additions', () => {
      let cvSkills: string[] = [];
      cvSkills = addSkillToCV(cvSkills, 'Python');
      cvSkills = addSkillToCV(cvSkills, 'Docker');
      cvSkills = addSkillToCV(cvSkills, 'Kubernetes');
      cvSkills = addSkillToCV(cvSkills, 'python'); // duplicate, should be ignored

      expect(cvSkills).toHaveLength(3);
    });
  });
});
