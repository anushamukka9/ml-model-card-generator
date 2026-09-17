"""Model card schema: structured, validated sections following the
Mitchell et al. "Model Cards for Model Reporting" framework, extended with
machine-readable fields so cards double as governance metadata."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


class CardValidationError(ValueError):
    """Raised when a model card fails validation."""


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
class SectionTrainingData:
    datasets: list[str] = field(default_factory=list)
    preprocessing: str = ""
    splits: dict[str, float] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors = []
        if not self.datasets:
            errors.append("training_data.datasets must name at least one dataset")
        total = sum(self.splits.values())
        if self.splits and not 0.99 <= total <= 1.01:
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
class ModelCard:
    """A complete, validated model card."""

    model_name: str
    version: str = "0.1.0"
    model_type: str = ""
    developers: str = ""
    intended_use: SectionIntendedUse = field(default_factory=SectionIntendedUse)
    training_data: SectionTrainingData = field(default_factory=SectionTrainingData)
    evaluation: SectionEvaluation = field(default_factory=SectionEvaluation)
    limitations: SectionLimitations = field(default_factory=SectionLimitations)
    ethical_considerations: SectionEthicalConsiderations = field(
        default_factory=SectionEthicalConsiderations
    )
    extra: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.model_name or not self.model_name.strip():
            errors.append("model_name is required")
        errors += [f"{e}" for e in self.intended_use.validate()]
        errors += [f"{e}" for e in self.training_data.validate()]
        errors += [f"{e}" for e in self.evaluation.validate()]
        errors += [f"{e}" for e in self.ethical_considerations.validate()]
        return errors

    def ensure_valid(self) -> None:
        errors = self.validate()
        if errors:
            raise CardValidationError("; ".join(errors))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelCard":
        data = dict(data)
        intended = SectionIntendedUse(**data.pop("intended_use", {}))
        training = SectionTrainingData(**data.pop("training_data", {}))
        eval_raw = data.pop("evaluation", {})
        metrics = [Metric(**m) for m in eval_raw.get("metrics", [])]
        evaluation = SectionEvaluation(
            metrics=metrics,
            evaluation_data=eval_raw.get("evaluation_data", ""),
            procedure=eval_raw.get("procedure", ""),
        )
        limitations = SectionLimitations(**data.pop("limitations", {}))
        ethical = SectionEthicalConsiderations(**data.pop("ethical_considerations", {}))
        return cls(
            intended_use=intended,
            training_data=training,
            evaluation=evaluation,
            limitations=limitations,
            ethical_considerations=ethical,
            **data,
        )
