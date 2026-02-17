# CoPilot Instructions / Coding Rules for AI CV Tailoring Tool

1. **Truth First**
   - Never invent skills, projects, or experience.
   - Only use data from the structured skill JSON.
   - Transferable skills can be reframed, but missing skills cannot be implied as done.

2. **Modular Design**
   - Separate JD parsing, skill matching, scoring, and LaTeX CV generation.
   - Each module should have clear inputs and outputs.
   - Use Pydantic or similar schema validation for all structured data.

3. **Prompt & Output Safety**
   - All LLM outputs must conform to JSON schema.
   - Validate output before use.
   - Any LaTeX injection must be sanitized to prevent compile errors.

4. **Scoring**
   - Implement ATS keyword match scoring.
   - Implement capability alignment scoring.
   - Allow configurable weightings for:
     - Stack alignment
     - Domain relevance
     - Seniority match
     - Sponsorship feasibility
   - Scoring must be reproducible.

5. **LaTeX CV Generation**
   - Use Jinja2 templates with placeholders.
   - Avoid graphics/icons.
   - Keep structure ATS-friendly.
   - Only fill sections provided by the template.
   - Validate that output compiles to PDF.

6. **Logging & Traceability**
   - Every CV generation must log:
     - JD parsed skills
     - Matching results (direct / transferable / missing)
     - Scoring breakdown
     - Rewriting changes
   - Store logs for auditing.

7. **Version Control**
   - Git commits should be atomic and descriptive.
   - Include unit tests for parsing, scoring, and LaTeX output.

8. **Configuration**
   - Base truth JSON should be editable but immutable for LLM reference.
   - Allow toggles for:
     - Positioning mode (conservative / balanced / aggressive)
     - Scoring thresholds
     - Learning mode (for skills you are currently acquiring)

9. **Testing**
   - Include unit tests for:
     - JD parsing
     - Skill matching
     - Score calculation
     - LaTeX rendering
   - Include end-to-end test with sample JD + base CV → PDF.

10. **Documentation**
    - Document every module, function, and JSON schema.
    - Include a README explaining setup, usage, and maintenance.

