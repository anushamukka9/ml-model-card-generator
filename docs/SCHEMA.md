# Model Card Schema

The schema follows Mitchell et al., *"Model Cards for Model Reporting"*
(2019), with machine-readable fields so each card doubles as governance
metadata consumable by policy engines.

## Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_name` | string | yes | Unique model identifier |
| `version` | string | no | Model version (default `0.1.0`) |
| `model_type` | string | no | Architecture family / base model |
| `developers` | string | no | Owning team or individual |
| `license` | string | no | License or usage terms |
| `contact` | string | no | Contact for questions about the model |
| `citation` | string | no | How to cite the model (paper, report ID) |
| `intended_use` | object | yes | `primary_uses` must be non-empty |
| `factors` | object | no | Relevant vs. actually evaluated factors |
| `training_data` | object | yes | `datasets` must be non-empty; `splits` must sum to ~1.0 |
| `evaluation` | object | yes | `metrics` must be non-empty; values must be numeric |
| `quantitative_analyses` | object | no | Unitary and intersectional disaggregated results |
| `limitations` | object | no | Known failure modes, bias risks |
| `ethical_considerations` | object | yes | `human_oversight` required |
| `caveats` | object | no | Caveats and deployment recommendations |
| `extra` | object | no | Free-form extension point (registry URIs, run IDs) |

## Sections

### intended_use
- `primary_uses` (list, required): what the model is built for
- `out_of_scope` (list): explicitly unsupported uses
- `users` (string): who should operate it

### factors
- `relevant_factors` (list): groups or conditions that could affect performance
  (demographics, instrumentation, environment)
- `evaluation_factors` (list): the factors actually evaluated

Validation fails if a relevant factor has no corresponding evaluation factor.
This is the check that keeps disaggregated evaluation honest: you cannot
list a risk factor and then never measure it.

### training_data
- `datasets` (list, required): named datasets with licensing notes
- `preprocessing` (string): cleaning, PII handling, dedup
- `splits` (map): split name to fraction; values must be numeric and sum to 1.0

### evaluation
- `metrics` (list of `{name, value, split, notes}`, required): `value` must be
  numeric (a non-numeric value is rejected at load time, not silently kept)
- `evaluation_data` (string): which data the metrics came from
- `procedure` (string): cross-validation, seeds, harness

### quantitative_analyses
- `unitary_results` (list of `{name, value, slice, notes}`): results broken
  down by one factor at a time
- `intersectional_results` (list of `{name, value, slice, notes}`): results
  for intersections of factors (the slices where models usually fail first)

### limitations
- `known_limitations` (list): failure modes you have observed
- `bias_risks` (list): groups or contexts where performance may degrade

### ethical_considerations
- `sensitive_data` (string): what sensitive data is involved
- `human_oversight` (string, required): how humans stay in the loop
- `mitigation_steps` (list): bias probes, audits, red-teaming cadence

### caveats
- `caveats` (list): what the card does not cover, where the numbers do not transfer
- `recommendations` (list): deployment guidance (confidence thresholds, review triggers)

## Validation rules

1. `model_name` non-empty; `metadata` itself must be a mapping.
2. At least one primary use, one dataset, one metric.
3. Metric `value` fields must be numeric; anything else is a load error.
4. Split fractions numeric and summing to 1.0 (+-0.01).
5. Every `factors.relevant_factors` entry must appear in `evaluation_factors`.
6. `human_oversight` described.
7. Unknown top-level keys are kept under `extra` (forward compatibility) and
   reported by `find_unknown_fields()`; `model-card validate` prints them as
   warnings.

Run `model-card validate --input metadata.yaml` to check a file, or
`ModelCard.from_dict(...).ensure_valid()` in Python.
