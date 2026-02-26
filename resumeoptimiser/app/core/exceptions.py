"""Domain-level exceptions.

Each exception carries a human-readable message and a machine-readable code
so that API error handlers can map them to HTTP responses without business
logic leaking into the API layer.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application errors."""

    code: str = "APP_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class CVParsingError(AppError):
    """Raised when the CV cannot be parsed into a structured format."""

    code = "CV_PARSING_ERROR"


class JobNormalizationError(AppError):
    """Raised when the job description cannot be normalized."""

    code = "JOB_NORMALIZATION_ERROR"


class EmbeddingError(AppError):
    """Raised when an embedding cannot be computed."""

    code = "EMBEDDING_ERROR"


class SimilarityError(AppError):
    """Raised when similarity scoring fails."""

    code = "SIMILARITY_ERROR"


class LLMError(AppError):
    """Raised when the LLM call fails or returns an unparseable response."""

    code = "LLM_ERROR"


class ValidationError(AppError):
    """Raised when a domain object fails business-rule validation."""

    code = "VALIDATION_ERROR"


class AgentExecutionError(AppError):
    """Raised when an agent fails during its execute() lifecycle."""

    code = "AGENT_EXECUTION_ERROR"

    def __init__(self, agent: str, message: str) -> None:
        super().__init__(f"[{agent}] {message}")
        self.agent = agent
