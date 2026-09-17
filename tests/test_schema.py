"""Tests for the model card schema and validation."""

import pytest

from model_card.schema import (
    CardValidationError,
    Metric,
    ModelCard,
    SectionEvaluation,
    SectionIntendedUse,
    SectionTrainingData,
    SectionEthicalConsiderations,
)


def valid_card() -> ModelCard:
    return ModelCard(
        model_name="test-model",
        intended_use=SectionIntendedUse(primary_uses=["classification"]),
        training_data=SectionTrainingData(datasets=["ds-1"]),
        evaluation=SectionEvaluation(metrics=[Metric(name="accuracy", value=0.9)]),
        ethical_considerations=SectionEthicalConsiderations(human_oversight="manual review"),
    )


def test_valid_card_passes():
    card = valid_card()
    assert card.validate() == []
    card.ensure_valid()


def test_missing_model_name_fails():
    card = valid_card()
    card.model_name = "  "
    assert any("model_name" in e for e in card.validate())
    with pytest.raises(CardValidationError):
        card.ensure_valid()


def test_missing_primary_uses_fails():
    card = valid_card()
    card.intended_use = SectionIntendedUse(primary_uses=[])
    assert any("primary_uses" in e for e in card.validate())


def test_split_fractions_must_sum_to_one():
    card = valid_card()
    card.training_data.splits = {"train": 0.8, "test": 0.5}
    assert any("splits" in e for e in card.validate())


def test_metrics_required():
    card = valid_card()
    card.evaluation = SectionEvaluation(metrics=[])
    assert any("metrics" in e for e in card.validate())


def test_from_dict_roundtrip():
    card = valid_card()
    clone = ModelCard.from_dict(card.to_dict())
    assert clone.model_name == "test-model"
    assert clone.evaluation.metrics[0].name == "accuracy"
    assert clone.validate() == []
