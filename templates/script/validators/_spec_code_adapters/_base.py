"""
_base.py — FrameworkAdapter abstract base class and NormalizedForm dataclasses.

Every adapter must inherit from FrameworkAdapter and implement extract_spec()
and extract_code(). The core validator (verify_spec_code.py) uses only
NormalizedForm objects — it never imports framework-specific code.

Constraints:
- No comparison logic here — comparison lives in verify_spec_code.py only.
- No framework-specific imports at module level — import lazily inside methods.
- extract_spec() and extract_code() must never raise; return [] on any error.

Custom Adapter SDK:
- See _example_adapter.py for a fully annotated reference implementation.
- See docs/contributing-adapters.md for the step-by-step contributor guide.
- Register your adapter in verify_spec_code.py ADAPTER_REGISTRY and open a PR.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# NormalizedField — shared across all NormalizedForm types
# ---------------------------------------------------------------------------

@dataclass
class NormalizedField:
    """
    A single named field with an optional type string.

    Used as a component inside every NormalizedForm type to represent
    parameters, flags, request/response fields, props, etc.

    Attributes:
        name: Field identifier as it appears in spec or code.
        type: Raw type string (e.g. 'str', 'int', 'List[str]', 'string').
              Empty string when the type cannot be determined.
    """
    name: str
    type: str


# ---------------------------------------------------------------------------
# NormalizedForm dataclasses — one per project type
# ---------------------------------------------------------------------------

@dataclass
class NormalizedStageContract:
    """
    Data Pipeline / ML Pipeline: one pipeline stage's I/O contract.

    Used by: AirflowAdapter, DagsterAdapter, PrefectAdapter.

    Attributes:
        stage_name:    Unique stage identifier (matches spec section heading and function name).
        input_fields:  Fields consumed by this stage (function parameters).
        output_fields: Fields produced by this stage (return type, Output class fields).
    """
    stage_name: str
    input_fields: list[NormalizedField] = field(default_factory=list)
    output_fields: list[NormalizedField] = field(default_factory=list)


@dataclass
class NormalizedEndpoint:
    """
    Web App / Microservices: one HTTP endpoint.

    Comparison key: f"{method.upper()}:{path}" — both must match for a hit.

    Used by: FastAPIAdapter, FlaskAdapter, ExpressAdapter.

    Attributes:
        method:          HTTP verb in uppercase (GET, POST, PUT, DELETE, PATCH).
        path:            URL path exactly as declared (e.g. '/orders/{id}').
        request_fields:  Body or query fields declared for the request.
        response_fields: Fields declared in the response body.
    """
    method: str
    path: str
    request_fields: list[NormalizedField] = field(default_factory=list)
    response_fields: list[NormalizedField] = field(default_factory=list)


@dataclass
class NormalizedCommand:
    """
    CLI Tool: one subcommand with its flags.

    Used by: ClickAdapter.

    Attributes:
        name:  Subcommand name (e.g. 'build', 'deploy').
        flags: CLI flags/options (name without leading dashes, type from annotation or default).
    """
    name: str
    flags: list[NormalizedField] = field(default_factory=list)


@dataclass
class NormalizedFunction:
    """
    Library / SDK or LLM Tool: one public callable.

    Used by: PythonLibraryAdapter, ToolSchemaAdapter (via ExampleAdapter).

    Attributes:
        name:        Function name as exported (must appear in __all__ or be public).
        params:      Positional and keyword parameters with type annotations.
        return_type: Return type string; empty string when unspecified.
    """
    name: str
    params: list[NormalizedField] = field(default_factory=list)
    return_type: str = ''


@dataclass
class NormalizedTool:
    """
    AI / LLM App: one tool definition (function callable by an LLM agent).

    Used by: ToolSchemaAdapter.

    Attributes:
        name:       Tool name as registered (must match OpenAI schema `name` or Python function name).
        parameters: Tool parameters with name and type.
    """
    name: str
    parameters: list[NormalizedField] = field(default_factory=list)


@dataclass
class NormalizedResource:
    """
    IaC / DevOps: one infrastructure resource.

    Comparison key: resource `name`. `resource_type` is stored for context but
    not used in the core comparison key — two resources with the same name but
    different types are still treated as the same item.

    Used by: TerraformAdapter, PulumiAdapter.

    Attributes:
        name:          Resource logical name (Terraform label / Pulumi resource name arg).
        resource_type: Provider resource type (e.g. 'aws_instance', 'Instance').
        config_keys:   Top-level attribute names declared in the resource block.
    """
    name: str
    resource_type: str
    config_keys: list[str] = field(default_factory=list)


@dataclass
class NormalizedScreen:
    """
    Mobile App: one screen or widget with its props.

    Used by: ReactNativeAdapter, FlutterAdapter.

    Attributes:
        name:  Screen/widget class or function name (PascalCase by convention).
        props: Props or constructor fields exposed by the screen.
    """
    name: str
    props: list[NormalizedField] = field(default_factory=list)


# ---------------------------------------------------------------------------
# FrameworkAdapter — abstract base class for all adapters
# ---------------------------------------------------------------------------

class FrameworkAdapter(ABC):
    """
    Abstract base class for all framework adapters.

    Subclasses implement extract_spec() and extract_code() only.
    verify_spec_code.py calls both methods and compares their output —
    no comparison or reporting logic belongs here.

    Quick-start:
        1. Subclass FrameworkAdapter.
        2. Implement extract_spec(spec_path) → list[<NormalizedForm>].
        3. Implement extract_code(src_path)  → list[<NormalizedForm>].
        4. Both lists must contain the same NormalizedForm subclass.
        5. Register in verify_spec_code.py ADAPTER_REGISTRY.
        6. See _example_adapter.py for a fully worked example.
        7. See docs/contributing-adapters.md for the contributor guide.

    Invariants:
        - Both methods must return [] (not raise) on any error condition.
        - Neither method may contain comparison logic.
        - No framework-specific imports at module level.
    """

    @abstractmethod
    def extract_spec(self, spec_path: str) -> list:
        """
        Parse the spec document at `spec_path` and return NormalizedForm objects.

        Args:
            spec_path: Path to the spec file (Markdown, YAML, JSON, etc.).

        Returns:
            List of NormalizedForm objects, one per declared item.
            Must return [] (not raise) if the file is missing or malformed.
        """
        ...

    @abstractmethod
    def extract_code(self, src_path: str) -> list:
        """
        Parse source code at `src_path` and return NormalizedForm objects.

        Args:
            src_path: Path to a single source file OR a directory to walk.

        Returns:
            List of NormalizedForm objects, one per discovered item.
            Must return [] (not raise) on parse errors or missing files.
        """
        ...
