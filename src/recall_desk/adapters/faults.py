from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable

from recall_desk.ports import Permanent, Transient, UnknownOutcome


class FaultKind(StrEnum):
    HTTP_429 = "HTTP_429"
    HTTP_401 = "HTTP_401"
    HTTP_500 = "HTTP_500"
    CONNECT_BEFORE_SEND = "CONNECT_BEFORE_SEND"
    APPLY_THEN_DROP = "APPLY_THEN_DROP"
    MUTATE_BEFORE = "MUTATE_BEFORE"


@dataclass(frozen=True)
class FaultRule:
    port: str
    method: str
    call_index: int
    kind: FaultKind
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class FaultPlan:
    rules: list[FaultRule] = field(default_factory=list)


def wrap_port(port: Any, port_name: str, plan: FaultPlan, mutator: Callable[[FaultRule], None] | None = None) -> Any:
    """Return a narrow fault-injecting proxy for simulator and demo calls."""
    calls: dict[str, int] = {}

    class FaultWrapped:
        def __getattr__(self, method: str) -> Any:
            target = getattr(port, method)
            if not callable(target):
                return target

            def invoke(*args: Any, **kwargs: Any) -> Any:
                calls[method] = calls.get(method, 0) + 1
                index = calls[method]
                rule = next((item for item in plan.rules if item.port == port_name and item.method == method and item.call_index in {0, index}), None)
                if rule is None:
                    return target(*args, **kwargs)
                if rule.kind == FaultKind.APPLY_THEN_DROP:
                    target(*args, **kwargs)
                    raise UnknownOutcome()
                if rule.kind == FaultKind.MUTATE_BEFORE:
                    if mutator:
                        mutator(rule)
                    return target(*args, **kwargs)
                if rule.kind == FaultKind.CONNECT_BEFORE_SEND:
                    raise Transient(retry_after=None, before_send=True)
                if rule.kind == FaultKind.HTTP_429:
                    raise Transient(retry_after=0, before_send=False)
                if rule.kind == FaultKind.HTTP_500:
                    raise Permanent(500, "fault injected")
                raise Permanent(401, "fault injected")

            return invoke

    return FaultWrapped()
