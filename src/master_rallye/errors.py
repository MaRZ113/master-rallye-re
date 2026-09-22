"""Structured errors for Master Rallye asset parsing."""
from __future__ import annotations

from dataclasses import dataclass


class MasterRallyeError(Exception):
    """Base exception for the research library."""


class BoundsError(MasterRallyeError):
    """A declared structure extends beyond the available bytes."""


class FormatError(MasterRallyeError):
    """A structurally invalid or unreasonable value was encountered."""


class ExportError(MasterRallyeError):
    """An interchange export could not be produced."""


class DxWriteError(ExportError):
    """A template-preserving DX write failed a safety gate."""


@dataclass(frozen=True)
class UnknownRecordEvidence:
    source: str
    offset: int
    tag: int
    context_start: int
    context_hex: str
    preceding_context: str | None


class UnknownRecordTagError(FormatError):
    def __init__(self, evidence: UnknownRecordEvidence):
        self.evidence = evidence
        super().__init__(
            f"unknown draw record tag {evidence.tag} at 0x{evidence.offset:X} "
            f"in {evidence.source}"
        )
