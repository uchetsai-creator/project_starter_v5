import importlib.util
from pathlib import Path

_VSC_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "verify_spec_code.py"
)
_spec = importlib.util.spec_from_file_location("verify_spec_code", _VSC_PATH)
vsc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vsc)


# ---------------------------------------------------------------------------
# _types_match / _normalize_type — spec-prose vs code-native type vocabulary
# ---------------------------------------------------------------------------

def test_string_str_are_equivalent():
    assert vsc._types_match("string", "str")


def test_boolean_bool_are_equivalent():
    assert vsc._types_match("boolean", "bool")


def test_integer_int_are_equivalent():
    assert vsc._types_match("integer", "int")


def test_case_insensitive():
    assert vsc._types_match("String", "STR")


def test_genuinely_different_types_still_mismatch():
    assert not vsc._types_match("boolean", "str")
    assert not vsc._types_match("string", "int")


def test_optional_wrapper_is_stripped():
    assert vsc._types_match("string", "Optional[str]")


def test_pipe_none_union_is_stripped():
    assert vsc._types_match("string", "str | None")


# ---------------------------------------------------------------------------
# compare() — field-level type_changed should respect the normalization
# ---------------------------------------------------------------------------

def test_compare_no_false_positive_for_equivalent_types():
    NF = vsc.NormalizedField
    NC = vsc.NormalizedCommand
    spec_items = [NC(name="build", flags=[NF(name="output", type="string")])]
    code_items = [NC(name="build", flags=[NF(name="output", type="str")])]
    report = vsc.compare(spec_items, code_items)
    assert report["field_mismatches"] == []
    assert report["missing_in_code"] == []
    assert report["extra_in_code"] == []


def test_curly_and_colon_path_params_are_equivalent():
    assert vsc._normalize_path("/orders/{id}") == vsc._normalize_path("/orders/:id")


def test_path_without_params_is_unchanged():
    assert vsc._normalize_path("/health") == "/health"


def test_compare_matches_endpoint_across_path_param_syntaxes():
    NE = vsc.NormalizedEndpoint
    spec_items = [NE(method="GET", path="/orders/{id}")]
    code_items = [NE(method="GET", path="/orders/:id")]
    report = vsc.compare(spec_items, code_items)
    assert report["missing_in_code"] == []
    assert report["extra_in_code"] == []


def test_compare_still_flags_real_type_mismatch():
    NF = vsc.NormalizedField
    NC = vsc.NormalizedCommand
    spec_items = [NC(name="build", flags=[NF(name="output", type="boolean")])]
    code_items = [NC(name="build", flags=[NF(name="output", type="str")])]
    report = vsc.compare(spec_items, code_items)
    assert len(report["field_mismatches"]) == 1
    assert report["field_mismatches"][0]["issue"] == "type_changed"


# ---------------------------------------------------------------------------
# NormalizedFunction.return_type — previously parsed on both sides but never
# actually compared by compare()
# ---------------------------------------------------------------------------

def test_return_type_mismatch_is_now_caught():
    NFn = vsc.NormalizedFunction
    spec_items = [NFn(name="parse_config", params=[], return_type="ConfigObject")]
    code_items = [NFn(name="parse_config", params=[], return_type="dict")]
    report = vsc.compare(spec_items, code_items)
    assert len(report["field_mismatches"]) == 1
    assert report["field_mismatches"][0]["field"] == "return"
    assert report["field_mismatches"][0]["issue"] == "type_changed"


def test_return_type_match_is_not_flagged():
    NFn = vsc.NormalizedFunction
    spec_items = [NFn(name="parse_config", params=[], return_type="dict")]
    code_items = [NFn(name="parse_config", params=[], return_type="dict")]
    report = vsc.compare(spec_items, code_items)
    assert report["field_mismatches"] == []


def test_return_type_equivalent_aliases_not_flagged():
    NFn = vsc.NormalizedFunction
    spec_items = [NFn(name="parse_config", params=[], return_type="boolean")]
    code_items = [NFn(name="parse_config", params=[], return_type="bool")]
    report = vsc.compare(spec_items, code_items)
    assert report["field_mismatches"] == []
