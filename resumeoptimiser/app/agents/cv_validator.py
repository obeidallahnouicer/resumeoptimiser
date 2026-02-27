"""CVValidatorAgent – applies business-rule validation to the optimised CV.

No LLM usage. Pure rule-based validation.

Rules:
- Contact email must be present.
- At least one experience or skills section must exist.
- No section may be empty after rewriting.
- Rewritten text must not be shorter than 50% of original (hallucination guard).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, ValidationError
from app.core.logging import get_logger
from app.schemas.cv import StructuredCVSchema
from app.schemas.report import OptimizedCVSchema

logger = get_logger(__name__)


@dataclass(frozen=True)
class CVValidatorInput:
    """Input for CVValidatorAgent."""

    original: StructuredCVSchema
    optimized: OptimizedCVSchema


@dataclass(frozen=True)
class CVValidatorOutput:
    """Output of CVValidatorAgent."""

    is_valid: bool
    violations: list[str]
    optimized: OptimizedCVSchema


class CVValidatorAgent(BaseAgent[CVValidatorInput, CVValidatorOutput]):
    """Validates an optimised CV against business rules (no LLM)."""

    meta = AgentMeta(name="CVValidatorAgent", version="1.0.0")

    def execute(self, input: CVValidatorInput) -> CVValidatorOutput:  # noqa: A002
        """Run all validation rules and return a validation result."""
        logger.info("cv_validator.start")
        violations = self._collect_violations(input)

        if violations:
            logger.warning("cv_validator.violations", count=len(violations))
        else:
            logger.info("cv_validator.success")

        return CVValidatorOutput(
            is_valid=len(violations) == 0,
            violations=violations,
            optimized=input.optimized,
        )

    def _collect_violations(self, input: CVValidatorInput) -> list[str]:  # noqa: A002
        """Run all rule checks and return a list of violation messages."""
        violations: list[str] = []
        violations.extend(self._check_contact(input.optimized))
        violations.extend(self._check_required_sections(input.optimized))
        violations.extend(self._check_no_empty_sections(input.optimized))
        violations.extend(self._check_no_drastic_shrinkage(input.original, input.optimized))
        return violations

    def _check_contact(self, cv: OptimizedCVSchema) -> list[str]:
        if not cv.contact.email:
            return ["Contact email is missing."]
        return []

    def _section_type_str(self, section_type: object) -> str:
        """Return the string value of a section_type whether it's an enum or a plain str."""
        return section_type.value if hasattr(section_type, "value") else str(section_type)

    def _check_required_sections(self, cv: OptimizedCVSchema) -> list[str]:
        types = {self._section_type_str(s.section_type) for s in cv.sections}
        if not types.intersection({"experience", "skills"}):
            return ["CV must contain at least one 'experience' or 'skills' section."]
        return []

    def _check_no_empty_sections(self, cv: OptimizedCVSchema) -> list[str]:
        return [
            f"Section '{self._section_type_str(s.section_type)}' is empty after rewriting."
            for s in cv.sections
            if not s.raw_text.strip()
        ]

    def _check_no_drastic_shrinkage(
        self,
        original: StructuredCVSchema,
        optimized: OptimizedCVSchema,
    ) -> list[str]:
        """Flag sections where the rewritten text is < 50% of the original."""
        violations: list[str] = []
        orig_map = {s.section_type: len(s.raw_text) for s in original.sections}
        for section in optimized.sections:
            orig_len = orig_map.get(section.section_type, 0)
            if orig_len > 0 and len(section.raw_text) < orig_len * 0.5:
                violations.append(
                    f"Section '{self._section_type_str(section.section_type)}' shrank by more than 50%."
                )
        return violations
