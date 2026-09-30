# ml-model-card-generator

**Generate standardized model cards from training metadata: Markdown + JSON output for governance.**

Model cards (Mitchell et al., 2019) are the industry-standard way to document
a model's intended use, training data, evaluation, limitations, and ethical
considerations. This tool turns a single metadata YAML file into both a
human-readable Markdown card and a machine-readable JSON document that plugs
straight into governance pipelines.

## Why

- **One source of truth**: write metadata once, publish Markdown for humans
  and JSON for policy engines.
- **Validated**: schema checks catch missing sections, non-numeric metrics,
  and unevaluated risk factors before a card ships.
- **CI-friendly**: `model-card validate` fails the build on incomplete cards.

## Install

```bash
pip install ml-model-card-generator
```

Or from source:

```bash
git clone https://github.com/anushamukka9/ml-model-card-generator
cd ml-model-card-generator
pip install -e ".[dev]"
```

## Quickstart

```bash
# Validate your metadata (warnings for unrecognized fields, errors fail)
model-card validate --input examples/metadata.yaml

# Render Markdown
model-card generate --input examples/metadata.yaml --output card.md

# Render machine-readable JSON
model-card generate --input examples/metadata.yaml --output card.json --format json
```

Or in Python:

```python
import yaml
from model_card.schema import ModelCard
from model_card.renderer import render_markdown, export_json

with open("metadata.yaml") as fh:
    card = ModelCard.from_dict(yaml.safe_load(fh))

card.ensure_valid()
print(render_markdown(card))   # for humans
print(export_json(card))       # for governance tooling
```

See `examples/quickstart.py`, and `examples/governance_export.py` for the
deployment-gate pattern: reading the JSON card in a policy check (oversight
documented, accuracy floor, all relevant factors evaluated).

## Metadata format

```yaml
model_name: sentiment-bert-v2
version: "2.1.0"
model_type: Fine-tuned transformer (BERT-base)
developers: NLP Platform Team
license: Internal use only
contact: nlp-platform@example.com
citation: Internal technical report TR-2026-041
intended_use:
  primary_uses: [Customer feedback sentiment classification]
  out_of_scope: [Legal or medical decision-making]
  users: Customer support operations teams
factors:
  relevant_factors: [Review language variety, Review length]
  evaluation_factors: [Review language variety, Review length]
training_data:
  datasets: [internal-support-tickets-2024, sst-2]
  preprocessing: Lowercased, deduplicated, PII redacted
  splits: {train: 0.8, validation: 0.1, test: 0.1}
evaluation:
  evaluation_data: Held-out test split
  procedure: 5-fold cross-validation
  metrics:
    - {name: accuracy, value: 0.934, split: test}
quantitative_analyses:
  unitary_results:
    - {name: accuracy, value: 0.887, slice: non-native English reviews}
  intersectional_results:
    - {name: accuracy, value: 0.871, slice: non-native English + short reviews}
limitations:
  known_limitations: [Degrades on sarcasm]
  bias_risks: [Skews toward North American interactions]
ethical_considerations:
  sensitive_data: Customer ticket text; PII redacted
  human_oversight: Low-confidence predictions routed to human agents
  mitigation_steps: [Quarterly bias probe]
caveats:
  caveats: [Metrics reflect the internal ticket distribution only]
  recommendations: [Route predictions below 0.6 confidence to humans]
```

Full field reference: [`docs/SCHEMA.md`](docs/SCHEMA.md). A complete example
lives in [`examples/metadata.yaml`](examples/metadata.yaml).

## API reference

| Piece | Description |
|---|---|
| `ModelCard.from_dict(data)` | Build a card from a metadata mapping; type-checks metrics and splits, keeps unknown top-level keys under `extra` |
| `card.validate()` / `card.ensure_valid()` | Return error list / raise `CardValidationError` |
| `find_unknown_fields(data)` | Unrecognized top-level keys (forward-compatibility warnings) |
| `render_markdown(card)` | Render through the bundled Jinja2 template |
| `export_json(card)` | Machine-readable JSON for governance tooling |
| Sections | `SectionIntendedUse`, `SectionFactors`, `SectionTrainingData`, `SectionEvaluation`, `SectionQuantitativeAnalyses`, `SectionLimitations`, `SectionEthicalConsiderations`, `SectionCaveats` |

## Customizing the template

The Markdown layout is a Jinja2 template at
`src/model_card/templates/card.md.j2`. Copy it into your project and point the
renderer at your own template directory to match your organization's branding.

## Production notes

- Unknown top-level metadata keys are preserved under `extra`, never dropped,
  so cards written against a newer schema still load. `model-card validate`
  warns about them.
- The factors check (every relevant factor must be an evaluated factor) is
  deliberately strict: it is the one validation rule that catches
  evaluation theater.
- JSON output is stable and key-sorted by construction order; diffing two
  cards' JSON is a reasonable change-review step.

## Roadmap

- [ ] Hugging Face Hub export (`README.md` model-card section)
- [ ] Diff command comparing two card versions
- [ ] Pre-commit hook for card validation

Contributions welcome: open an issue with the section your team needs.

## License

MIT: see [LICENSE](LICENSE).
