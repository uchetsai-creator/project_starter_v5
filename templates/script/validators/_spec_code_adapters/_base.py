"""
_base.py — FrameworkAdapter abstract base class and NormalizedForm dataclasses.

Every adapter must inherit from FrameworkAdapter and implement extract_spec()
and extract_code(). The core validator (verify_spec_code.py) uses only
NormalizedForm objects — it never imports framework-specific code.

Constraints:
- No comparison logic here — comparison lives in verify_spec_code.py only.
- No framework-specific imports at module level — import lazily inside methods.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# NormalizedField — shared across all NormalizedForm types
# ---------------------------------------------------------------------------

@dataclass
class NormalizedField:
    name: str
    type: str  # raw type string as declared in spec or code


# ---------------------------------------------------------------------------
# NormalizedForm dataclasses (one per project type)
# ---------------------------------------------------------------------------

@dataclass
class NormalizedStageContract:
    """Data Pipeline / ML Pipeline: one stage's input/output contract."""
    stage_name: str
    input_fields: list[NormalizedField] = field(default_factory=list)
    output_fields: list[NormalizedField] = field(default_factory=list)


@dataclass
class NormalizedEndpoint:
    """Web App / Microservices: one HTTP endpoint."""
    method: str
    path: str
    request_fields: list[NormalizedField] = field(default_factory=list)
    response_fields: list[NormalizedField] = field(default_factory=list)


@dataclass
class NormalizedCommand:
    """CLI Tool: one subcommand."""
    name: str
    flags: list[NormalizedField] = field(default_factory=list)


@dataclass
class NormalizedFunction:
    """Library / SDK: one public function."""
    name: str
    params: list[NormalizedField] = field(default_factory=list)
    return_type: str = ''


@dataclass
class NormalizedTool:
    """AI / LLM App: one tool definition."""
    name: str
    parameters: list[NormalizedField] = field(default_factory=list)


@dataclass
class NormalizedResource:
    """IaC / DevOps: one infrastructure resource."""
    name: str
    resource_type: str
    config_keys: list[str] = field(default_factory=list)


@dataclass
class NormalizedScreen:
    """Mobile App: one screen."""
    name: str
    props: list[NormalizedField] = field(default_factory=list)


# ---------------------------------------------------------------------------
# FrameworkAdapter abstract base class
# ---------------------------------------------------------------------------

class FrameworkAdapter(ABC):
    """
    Abstract base class for all framework adapters.

    Subclasses implement extract_spec() and extract_code() only.
    The returned lists contain NormalizedForm objects that verify_spec_code.py
    then compares — no comparison logic belongs here.
    """

    @abstractmethod
    def extract_spec(self, spec_path: str) -> list:
        """Parse the spec document and return a list of NormalizedForm objects."""
        ...

    @abstractmethod
    def extract_code(self, src_path: str) -> list:
        """Parse the source code and return a list of NormalizedForm objects."""
        ...
