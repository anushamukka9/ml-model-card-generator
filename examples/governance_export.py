"""Governance export: consume the machine-readable JSON card in a policy check.

This is the pattern the JSON export exists for: a deployment gate reads the
card and enforces policy (oversight documented, accuracy above a floor, no
unevaluated risk factors) before a model ships.
"""

import json
from pathlib import Path

import yaml

from model_card.renderer import export_json
from model_card.schema import ModelCard

BASE = Path(__file__).resolve().parent.parent
with open(BASE / "examples" / "metadata.yaml", encoding="utf-8") as fh:
    card = ModelCard.from_dict(yaml.safe_load(fh))
card.ensure_valid()

payload = json.loads(export_json(card))

checks = []


def check(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, ok, detail))


# Policy 1: human oversight must be documented.
check(
    "human oversight documented",
    bool(payload["ethical_considerations"]["human_oversight"]),
)

# Policy 2: headline accuracy on the test split must clear 0.90.
accuracies = [
    m["value"] for m in payload["evaluation"]["metrics"]
    if m["name"] == "accuracy" and m["split"] == "test"
]
check("test accuracy >= 0.90", bool(accuracies) and min(accuracies) >= 0.90,
      f"min={min(accuracies) if accuracies else 'n/a'}")

# Policy 3: every relevant factor must have been evaluated.
relevant = set(payload["factors"]["relevant_factors"])
evaluated = set(payload["factors"]["evaluation_factors"])
check("all relevant factors evaluated", relevant <= evaluated,
      f"unevaluated={sorted(relevant - evaluated)}")

# Policy 4: weakest reported slice must stay within 10 points of headline.
unitary = [r["value"] for r in payload["quantitative_analyses"]["unitary_results"]]
if unitary and accuracies:
    check("weakest slice within 10 pts of headline",
          min(unitary) >= min(accuracies) - 0.10,
          f"weakest={min(unitary):.3f}")

failed = [name for name, ok, _ in checks if not ok]
for name, ok, detail in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
raise SystemExit(1 if failed else 0)
