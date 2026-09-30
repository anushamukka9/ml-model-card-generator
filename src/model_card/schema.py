"""Model card schema: structured, validated sections following the
Mitchell et al. "Model Cards for Model Reporting" framework, extended with
machine-readable fields so cards double as governance metadata.

Sections: model details (top level), intended use, factors, training data,
evaluation, quantitative analyses, limitations, ethical considerations, and
caveats/recommendations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


class CardValidationError(ValueError):
    """Raised when a model card fails validation."""


# ---------------------------------------------------------------------------
# Helpers for building sections from raw metadata dicts
# ---------------------------------------------------------------------------

def _require_mapping(raw: Any, where: str) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise CardValidationError(f"{where} must be a mapping, got {type(raw).__name__}")
    return raw


def _known_fields(cls) -> set[str]:
    return {f.name for f in fields(cls)}


def _build_section(raw: Any, cls, where: str):
    """Build a section dataclass, ignoring (not failing on) unknown keys.

    Unknown keys are reported separately by :func:`find_unknown_fields` at
    the top level; nested unknown keys are dropped to keep cards forward
    compatible with newer schema versions.
    """
    data = _require_mapping(raw, where)
    known = _known_fields(cls)
    return cls(**{k: v for k, v in data.items() if k in known})


def _metric_from_raw(raw: Any, index: int) -> Metric:
    data = _require_mapping(raw, f"evaluation.metrics[{index}]")
    name = data.get("name", "")
    if not isinstance(name, str) or not name.strip():
        raise CardValidationError(f"evaluation.metrics[{index}].name must be a non-empty string")
    value = data.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CardValidationError(
            f"evaluation.metrics[{index}].value must be numeric, got {value!r}"
        )
    return Metric(
        name=name,
        value=float(value),
        split=str(data.get("split", "test")),
        notes=str(data.get("notes", "")),
    )


def _analysis_from_raw(raw: Any, where: str, index: int) -> AnalysisResult:
    data = _require_mapping(raw, f"{where}[{index}]")
    name = data.get("name", "")
    if not isinstance(name, str) or not name.strip():
        raise CardValidationError(f"{where}[{index}].name must be a non-empty string")
    value = data.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CardValidationError(f"{where}[{index}].value must be numeric, got {value!r}")
    return AnalysisResult(
        name=name,
        value=float(value),
        slice=str(data.get("slice", "overall")),
        notes=str(data.get("notes", "")),
    )


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

@dataclass
class SectionIntendedUse:
    primary_uses: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    users: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not self.primary_uses:
            errors.append("intended_use.primary_uses must list at least one primary use")
        return errors


@dataclass
class SectionFactors:
    """Factors relevant to model performance (Mitchell et al. "Factors").

    ``relevant_factors`` names groups or conditions that could affect
    performance; ``evaluation_factors`` names the ones actually evaluated.
    """

    relevant_factors: list[str] = field(default_factory=list)
    evaluation_factors: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        unevaluated = [f for f in self.relevant_factors if f not in self.evaluation_factors]
        if unevaluated:
            errors.append(
                "factors: relevant factors not covered by evaluation: "
                + ", ".join(unevaluated)
            )
        return errors


@dataclass
class SectionTrainingData:
    datasets: list[str] = field(default_factory=list)
    preprocessing: str = ""
    splits: dict[str, float] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors = []
        if not self.datasets:
            errors.append("training_data.datasets must name at least one dataset")
        if self.splits:
            bad = [k for k, v in self.splits.items()
                   if isinstance(v, bool) or not isinstance(v, (int, float))]
            if bad:
                errors.append(f"training_data.splits values must be numeric: {bad}")
            else:
                total = sum(self.splits.values())
                if not 0.99 <= total <= 1.01:
                    errors.append(f"training_data.splits must sum to ~1.0, got {total:.3f}")
        return errors


@dataclass
class Metric:
    name: str
    value: float
    split: str = "test"
    notes: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not self.name:
            errors.append("evaluation.metrics[].name is required")
        return errors


@dataclass
class SectionEvaluation:
    metrics: list[Metric] = field(default_factory=list)
    evaluation_data: str = ""
    procedure: str = ""

    def validate(self) -> list[str]:
        errors = [e for m in self.metrics for e in m.validate()]
        if not self.metrics:
            errors.append("evaluation.metrics must contain at least one metric")
        return errors


@dataclass
class AnalysisResult:
    """One quantitative result, optionally sliced by a factor."""

    name: str
    value: float
    slice: str = "overall"
    notes: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not self.name:
            errors.append("quantitative_analyses results need a name")
        return errors


@dataclass
class SectionQuantitativeAnalyses:
    """Disaggregated results: unitary (one factor) and intersectional."""

    unitary_results: list[AnalysisResult] = field(default_factory=list)
    intersectional_results: list[AnalysisResult] = field(default_factory=list)

    def validate(self) -> list[str]:
        return [
            e
            for r in self.unitary_results + self.intersectional_results
            for e in r.validate()
        ]


@dataclass
class SectionLimitations:
    known_limitations: list[str] = field(default_factory=list)
    bias_risks: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        return []


@dataclass
class SectionEthicalConsiderations:
    sensitive_data: str = ""
    human_oversight: str = ""
    mitigation_steps: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        if not self.human_oversight:
            errors.append("ethical_considerations.human_oversight must describe oversight")
        return errors


@dataclass
class SectionCaveats:
    """Caveats and recommendations for deployment."""

    caveats: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        return []


# ---------------------------------------------------------------------------
# The card
# ---------------------------------------------------------------------------

# Top-level scalar fields (everything else is a section or `extra`).
_TOP_LEVEL_SCALARS = (
    "model_name", "version", "model_type", "developers",
    "license", "contact", "citation",
)
_SECTION_KEYS = (
    "intended_use", "factors", "training_data", "evaluation",
    "quantitative_analyses", "limitations", "ethical_considerations", "caveats",
)


def find_unknown_fields(data: dict[str, Any]) -> list[str]:
    """Top-level metadata keys the schema does not recognize.

    Unknown keys are kept (see ``ModelCard.extra``) rather than rejected, so
    newer metadata stays loadable; this helper lets tooling warn about them.
    """
    known = set(_TOP_LEVEL_SCALARS) | set(_SECTION_KEYS) | {"extra"}
    return sorted(k for k in data if k not in known)


@dataclass
class ModelCard:
    """A complete, validated model card."""

    model_name: str
    version: str = "0.1.0"
    model_type: str = ""
    developers: str = ""
    license: str = ""
    contact: str = ""
    citation: str = ""
    intended_use: SectionIntendedUse = field(default_factory=SectionIntendedUse)
    factors: SectionFactors = field(default_factory=SectionFactors)
    training_data: SectionTrainingData = field(default_factory=SectionTrainingData)
    evaluation: SectionEvaluation = field(default_factory=SectionEvaluation)
    quantitative_analyses: SectionQuantitativeAnalyses = field(
        default_factory=SectionQuantitativeAnalyses
    )
    limitations: SectionLimitations = field(default_factory=SectionLimitations)
    ethical_considerations: SectionEthicalConsiderations = field(
        default_factory=SectionEthicalConsiderations
    )
    caveats: SectionCaveats = field(default_factory=SectionCaveats)
    extra: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.model_name or not self.model_name.strip():
            errors.append("model_name is required")
        errors += self.intended_use.validate()
        errors += self.factors.validate()
        errors += self.training_data.validate()
        errors += self.evaluation.validate()
        errors += self.quantitative_analyses.validate()
        errors += self.ethical_considerations.validate()
        return errors

    def ensure_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise CardValidationError("; ".join(errors))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelCard:
        data = _require_mapping(data, "metadata")

        intended = _build_section(data.get("intended_use"), SectionIntendedUse, "intended_use")
        factor_data = _require_mapping(data.get("factors"), "factors")
        factor_list = factor_data.get("relevant_factors", []) or []
        eval_factor_list = factor_data.get("evaluation_factors", []) or []
        factors = SectionFactors(
            relevant_factors=[str(f) for f in factor_list],
            evaluation_factors=[str(f) for f in eval_factor_list],
        )
        training = _build_section(data.get("training_data"), SectionTrainingData, "training_data")

        eval_raw = _require_mapping(data.get("evaluation"), "evaluation")
        metrics_raw = eval_raw.get("metrics", []) or []
        if not isinstance(metrics_raw, list):
            raise CardValidationError("evaluation.metrics must be a list")
        metrics = [_metric_from_raw(m, i) for i, m in enumerate(metrics_raw)]
        evaluation = SectionEvaluation(
            metrics=metrics,
            evaluation_data=str(eval_raw.get("evaluation_data", "") or ""),
            procedure=str(eval_raw.get("procedure", "") or ""),
        )

        quant_raw = _require_mapping(data.get("quantitative_analyses"), "quantitative_analyses")
        unitary_raw = quant_raw.get("unitary_results", []) or []
        inter_raw = quant_raw.get("intersectional_results", []) or []
        if not isinstance(unitary_raw, list) or not isinstance(inter_raw, list):
            raise CardValidationError("quantitative_analyses results must be lists")
        quantitative_analyses = SectionQuantitativeAnalyses(
            unitary_results=[
                _analysis_from_raw(r, "quantitative_analyses.unitary_results", i)
                for i, r in enumerate(unitary_raw)
            ],
            intersectional_results=[
                _analysis_from_raw(r, "quantitative_analyses.intersectional_results", i)
                for i, r in enumerate(inter_raw)
            ],
        )

        limitations = _build_section(data.get("limitations"), SectionLimitations, "limitations")
        ethical = _build_section(
            data.get("ethical_considerations"), SectionEthicalConsiderations,
            "ethical_considerations",
        )
        caveats = _build_section(data.get("caveats"), SectionCaveats, "caveats")

        scalars = {
            k: str(data.get(k, "") or "")
            for k in _TOP_LEVEL_SCALARS
            if k != "model_name"
        }
        model_name = data.get("model_name", "")
        if not isinstance(model_name, str):
            raise CardValidationError("model_name must be a string")

        extra = _require_mapping(data.get("extra"), "extra")
        for key in find_unknown_fields(data):
            extra[key] = data[key]

        return cls(
            model_name=model_name,
            intended_use=intended,
            factors=factors,
            training_data=training,
            evaluation=evaluation,
            quantitative_analyses=quantitative_analyses,
            limitations=limitations,
            ethical_considerations=ethical,
            caveats=caveats,
            extra=dict(extra),
            **scalars,
        )
