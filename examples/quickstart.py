"""Quickstart: build a model card from the example metadata file."""

from pathlib import Path

import yaml

from model_card.renderer import export_json, render_markdown
from model_card.schema import ModelCard

BASE = Path(__file__).resolve().parent.parent

with open(BASE / "examples" / "metadata.yaml", encoding="utf-8") as fh:
    metadata = yaml.safe_load(fh)

card = ModelCard.from_dict(metadata)
card.ensure_valid()

print("=== MARKDOWN (first 25 lines) ===")
print("\n".join(render_markdown(card).splitlines()[:25]))
print("\n=== JSON keys ===")
import json

print(sorted(json.loads(export_json(card)).keys()))
print("\nCard validated and rendered successfully.")
