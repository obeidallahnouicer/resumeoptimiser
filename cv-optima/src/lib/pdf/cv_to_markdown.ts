/**
 * cv_to_markdown.ts
 *
 * Responsibility: convert an OptimizedCV into a clean Markdown string.
 *
 * The resulting Markdown is the single source of truth for both the
 * live preview and the final PDF download. Users can edit it freely
 * before printing.
 *
 * Format contract:
 *   # NAME
 *   contact line
 *   ---
 *   ## SECTION TITLE
 *   **Job Title, Company (dates)**
 *   body text
 *   - bullet
 */

import type { OptimizedCV, CVSection } from '../../types/pipeline';

// ---------------------------------------------------------------------------
// Section label map (mirrors layout_tokens.ts — kept separate, no dep)
// ---------------------------------------------------------------------------

const SECTION_LABELS: Record<string, string> = {
  summary:        'Professional Summary',
  experience:     'Experience',
  education:      'Education',
  skills:         'Skills',
  certifications: 'Certifications',
  projects:       'Projects',
  languages:      'Languages',
  other:          'Additional Information',
};

function sectionLabel(type: string): string {
  return SECTION_LABELS[type] ?? type.charAt(0).toUpperCase() + type.slice(1);
}

// ---------------------------------------------------------------------------
// Item renderers
// ---------------------------------------------------------------------------

/**
 * For experience / education: detect "Header: body" pattern and render as
 * bold header + indented body. Falls back to plain bullet.
 */
function renderEntryItem(item: string): string {
  const colonIdx = item.indexOf(':');
  if (colonIdx >= 5 && colonIdx <= 200) {
    const header = item.slice(0, colonIdx).trim();
    const body   = item.slice(colonIdx + 1).trim();
    if (body) {
      return `**${header}**\n${body}`;
    }
  }
  return `**${item}**`;
}

function renderBulletItem(item: string): string {
  return `- ${item}`;
}

// ---------------------------------------------------------------------------
// Section renderer
// ---------------------------------------------------------------------------

function renderSection(section: CVSection): string {
  const heading = `## ${sectionLabel(section.section_type).toUpperCase()}`;

  const usesEntryFormat =
    section.section_type === 'experience' || section.section_type === 'education';

  let body = '';

  if (section.items.length > 0) {
    if (usesEntryFormat) {
      body = section.items.map(item => `\n${renderEntryItem(item)}`).join('\n');
    } else {
      body = `\n${section.items.map(renderBulletItem).join('\n')}`;
    }
  } else if (section.raw_text.trim()) {
    body = `\n${section.raw_text.trim()}`;
  }

  return `${heading}${body}`;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Convert an OptimizedCV into a Markdown string.
 * Deterministic: same input → same output.
 */
export function cvToMarkdown(cv: OptimizedCV): string {
  const { contact, sections } = cv;

  const contactParts = [
    contact.email,
    contact.phone,
    contact.location,
    contact.linkedin,
    contact.github,
  ].filter(Boolean);

  const contactLine = contactParts.length > 0 ? contactParts.join('  |  ') : '';
  const nameHeading = `# ${(contact.name || 'Candidate').toUpperCase()}`;
  const sectionBlocks = sections.map(renderSection).join('\n\n');

  return [nameHeading, contactLine, '---', sectionBlocks]
    .filter(Boolean)
    .join('\n\n')
    .trimEnd();
}
