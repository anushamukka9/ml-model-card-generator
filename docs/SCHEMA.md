# Model Card Schema

The schema follows Mitchell et al., *"Model Cards for Model Reporting"*
(2019), with machine-readable fields so each card doubles as governance
metadata consumable by policy engines (e.g. `ai-policy-guard`).

## Top-level fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_name` | string | yes | Unique model identifier |
| `version` | string | no | Model version (default `0.1.0`) |
| `model_type` | string | no | Architecture family / base model |
| `developers` | string | no | Owning team or individual |
| `intended_use` | object | yes | `primary_uses` must be non-empty |
| `training_data` | object | yes | `datasets` must be non-empty; `splits` must sum to ~1.0 |
| `evaluation` | object | yes | `metrics` must be non-empty |
| `limitations` | object | no | Known failure modes, bias risks |
| `ethical_considerations` | object | yes | `human_oversight` required |
| `extra` | object | no | Free-form extension point (registry URIs, run IDs) |

## Sections

### intended_use
- `primary_uses` (list, required): what the model is built for
- `out_of_scope` (list): explicitly unsupported uses
- `users` (string): who should operate it

### training_data
- `datasets` (list, required): named datasets with licensing notes
- `preprocessing` (string): cleaning, PII handling, dedup
- `splits` (map): split name → fraction, must sum to 1.0

### evaluation
- `metrics` (list of `{name, value, split, notes}`, required)
- `evaluation_data` (string): which data the metrics came from
- `procedure` (string): cross-validation, seeds, harness

### limitations
- `known_limitations` (list): failure modes you have observed
- `bias_risks` (list): groups or contexts where performance may degrade

### ethical_considerations
- `sensitive_data` (string): what sensitive data is involved
- `human_oversight` (string, required): how humans stay in the loop
- `mitigation_steps` (list): bias probes, audits, red-teaming cadence

## Validation rules

1. `model_name` non-empty.
2. At least one primary use, one dataset, one metric.
3. Split fractions sum to 1.0 (±0.01).
4. `human_oversight` described.

Run `model-card validate --input metadata.yaml` to check a file, or
`ModelCard.from_dict(...).ensure_valid()` in Python.
