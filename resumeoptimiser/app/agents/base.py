"""Base Agent Protocol and supporting types.

Every agent in the system must satisfy the Agent[I, O] Protocol:
  - Single public method: execute(input: I) -> O
  - Generic over input/output types
  - No shared mutable state
  - Fully injectable (all dependencies via constructor)

Usage::

    class MyAgent:
        def execute(self, input: MyInput) -> MyOutput:
            ...

    def run(agent: Agent[MyInput, MyOutput], data: MyInput) -> MyOutput:
        return agent.execute(data)
"""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar, runtime_checkable

I = TypeVar("I")   # Input schema type
O = TypeVar("O")   # Output schema type  # noqa: E741


@runtime_checkable
class Agent(Protocol[I, O]):
    """Structural protocol that every agent must satisfy.

    By using Protocol instead of ABC we:
    - Avoid forcing inheritance chains
    - Allow duck-typing (any class with execute() qualifies)
    - Keep agents independently testable
    """

    def execute(self, input: I) -> O:  # noqa: A002
        """Run the agent's single responsibility.

        Args:
            input: Strictly-typed Pydantic schema instance.

        Returns:
            Strictly-typed Pydantic schema instance.

        Raises:
            AgentExecutionError: On any agent-level failure.
        """
        ...


class AgentMeta:
    """Lightweight metadata descriptor for an agent.

    Attach this to an agent class to make it self-describing –
    useful for logging, tracing, and the pipeline orchestrator.
    """

    def __init__(self, name: str, version: str = "1.0.0") -> None:
        self.name = name
        self.version = version

    def __repr__(self) -> str:
        return f"AgentMeta(name={self.name!r}, version={self.version!r})"


class BaseAgent(Generic[I, O]):
    """Optional concrete base offering metadata and error wrapping.

    Agents may inherit this or implement Agent[I, O] directly.
    Inheriting is opt-in – never mandatory.
    """

    meta: AgentMeta

    def execute(self, input: I) -> O:  # noqa: A002
        raise NotImplementedError(f"{self.__class__.__name__} must implement execute()")
