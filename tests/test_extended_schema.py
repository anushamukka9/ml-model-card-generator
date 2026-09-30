"""Tests for the extended schema: factors, quantitative analyses, caveats,
top-level details, and input validation."""

import json

import pytest
import yaml

from model_card.renderer import export_json, render_markdown
from model_card.schema import (
    CardValidationError,
    ModelCard,
    find_unknown_fields,
)


def base_metadata() -> dict:
    return {
        "model_name": "test-model",
        "intended_use": {"primary_uses": ["classification"]},
        "training_data": {"datasets": ["ds-1"]},
        "evaluation": {"metrics": [{"name": "accuracy", "value": 0.9}]},
        "ethical_considerations": {"human_oversight": "manual review"},
    }


def test_new_sections_roundtrip():
    data = base_metadata()
    data.update({
        "license": "Apache-2.0",
        "contact": "team@example.com",
        "citation": "TR-2026-001",
        "factors": {
            "relevant_factors": ["dialect"],
            "evaluation_factors": ["dialect"],
        },
        "quantitative_analyses": {
            "unitary_results": [
                {"name": "accuracy", "value": 0.91, "slice": "dialect A"},
            ],
            "intersectional_results": [
                {"name": "accuracy", "value": 0.84, "slice": "dialect A + short"},
            ],
        },
        "caveats": {
            "caveats": ["Untested on long documents"],
            "recommendations": ["Human review below 0.6 confidence"],
        },
    })
    card = ModelCard.from_dict(data)
    assert card.validate() == []
    clone = ModelCard.from_dict(card.to_dict())
    assert clone.license == "Apache-2.0"
    assert clone.factors.evaluation_factors == ["dialect"]
    assert clone.quantitative_analyses.unitary_results[0].value == pytest.approx(0.91)
    assert clone.caveats.recommendations == ["Human review below 0.6 confidence"]


def test_unevaluated_relevant_factor_fails():
    data = base_metadata()
    data["factors"] = {"relevant_factors": ["dialect", "age"], "evaluation_factors": ["dialect"]}
    card = ModelCard.from_dict(data)
    assert any("age" in e for e in card.validate())


def test_non_numeric_metric_value_rejected():
    data = base_metadata()
    data["evaluation"]["metrics"] = [{"name": "accuracy", "value": "high"}]
    with pytest.raises(CardValidationError, match="must be numeric"):
        ModelCard.from_dict(data)


def test_non_numeric_split_rejected():
    data = base_metadata()
    data["training_data"]["splits"] = {"train": "most", "test": 0.2}
    card = ModelCard.from_dict(data)
    assert any("splits" in e for e in card.validate())


def test_unknown_top_level_keys_kept_in_extra():
    data = base_metadata()
    data["registry_uri"] = "models://team/test-model"
    assert find_unknown_fields(data) == ["registry_uri"]
    card = ModelCard.from_dict(data)
    assert card.extra["registry_uri"] == "models://team/test-model"
    assert card.validate() == []


def test_non_mapping_metadata_rejected():
    with pytest.raises(CardValidationError):
        ModelCard.from_dict(["not", "a", "mapping"])


def test_render_includes_new_sections():
    with open("examples/metadata.yaml", encoding="utf-8") as fh:
        card = ModelCard.from_dict(yaml.safe_load(fh))
    md = render_markdown(card)
    for heading in ("## Factors", "## Quantitative Analyses",
                    "## Caveats and Recommendations"):
        assert heading in md, heading
    assert "Apache-2.0" not in md  # example uses its own license
    assert "Internal use only" in md
    assert "non-native English + short reviews" in md


def test_render_skips_empty_optional_sections():
    card = ModelCard.from_dict(base_metadata())
    md = render_markdown(card)
    assert "## Factors" not in md
    assert "## Quantitative Analyses" not in md
    assert "## Caveats and Recommendations" not in md


def test_json_export_has_new_sections():
    card = ModelCard.from_dict(base_metadata())
    payload = json.loads(export_json(card))
    for key in ("factors", "quantitative_analyses", "caveats",
                "license", "contact", "citation"):
        assert key in payload, key
