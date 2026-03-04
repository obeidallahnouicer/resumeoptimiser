/**
 * cv_document.ts
 *
 * Responsibility: document object model for a CV.
 *
 * Rules:
 *  - Immutable sections by default.
 *  - `updateSection` replaces only the explicitly targeted section.
 *  - Untouched sections are returned as-is (reference equality preserved).
 *  - Section order is always preserved.
 *  - No rendering logic here.
 *  - No business / scoring logic here.
 */

import type { ContactInfo, CVSection, SectionType } from '../../types/pipeline';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** A section that has been explicitly queued for replacement. */
export interface SectionUpdate {
  sectionType: SectionType;
  newContent: CVSection;
}

// ---------------------------------------------------------------------------
// CVDocument
// ---------------------------------------------------------------------------

export class CVDocument {
  /** Ordered list of CV sections. Never mutated in place. */
  readonly sections: ReadonlyArray<CVSection>;

  /** Contact block – treated as immutable unless explicitly replaced. */
  readonly contact: ContactInfo;

  constructor(contact: ContactInfo, sections: ReadonlyArray<CVSection>) {
    this.contact  = contact;
    this.sections = sections;
  }

  /**
   * Return a new CVDocument with exactly one section replaced.
   *
   * - The replacement slot is found by `sectionType`.
   * - If the section type does not exist → throw RangeError (never silently append).
   * - All other sections are preserved by reference.
   * - Order is preserved.
   */
  updateSection(sectionType: SectionType, newContent: CVSection): CVDocument {
    const idx = this.sections.findIndex(s => s.section_type === sectionType);
    if (idx === -1) {
      throw new RangeError(
        `[CVDocument] Cannot update section "${sectionType}": not found in document.`,
      );
    }

    const updated = this.sections.map((s, i) => (i === idx ? newContent : s));
    return new CVDocument(this.contact, updated);
  }

  /**
   * Apply a batch of section updates in declaration order.
   * Returns a new CVDocument; original is untouched.
   */
  applyUpdates(updates: ReadonlyArray<SectionUpdate>): CVDocument {
    return updates.reduce<CVDocument>(
      (doc, u) => doc.updateSection(u.sectionType, u.newContent),
      this,
    );
  }

  /**
   * Return the section matching `sectionType`, or `undefined`.
   * Read-only – callers must not mutate the returned object.
   */
  getSection(sectionType: SectionType): CVSection | undefined {
    return this.sections.find(s => s.section_type === sectionType);
  }

  /**
   * Check whether a section of the given type exists.
   */
  hasSection(sectionType: SectionType): boolean {
    return this.sections.some(s => s.section_type === sectionType);
  }
}

// ---------------------------------------------------------------------------
// Factory helpers
// ---------------------------------------------------------------------------

/**
 * Build a CVDocument from a flat OptimizedCV-shaped object.
 * Accepts any object with `contact` and `sections` fields.
 */
export function buildCVDocument(cv: {
  contact: ContactInfo;
  sections: CVSection[];
}): CVDocument {
  if (!cv.contact) {
    throw new TypeError('[CVDocument] buildCVDocument: cv.contact is required.');
  }
  if (!Array.isArray(cv.sections)) {
    throw new TypeError('[CVDocument] buildCVDocument: cv.sections must be an array.');
  }
  return new CVDocument(cv.contact, cv.sections);
}
