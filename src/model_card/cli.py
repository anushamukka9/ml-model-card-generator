"""CLI: model-card generate --input metadata.yaml --output card.md"""

from __future__ import annotations

import sys
from pathlib import Path

import click
import yaml

from .renderer import export_json, render_markdown
from .schema import CardValidationError, ModelCard


@click.group()
def main() -> None:
    """Generate standardized model cards from training metadata."""


@main.command("generate")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="YAML metadata file describing the model.")
@click.option("--output", "output_path", required=True, type=click.Path(),
              help="Where to write the rendered card.")
@click.option("--format", "out_format", type=click.Choice(["markdown", "json"]),
              default="markdown", help="Output format.")
@click.option("--strict/--no-strict", default=True,
              help="Fail when validation finds problems (default: strict).")
def generate(input_path: str, output_path: str, out_format: str, strict: bool) -> None:
    """Render a model card from a metadata YAML file."""
    with open(input_path, encoding="utf-8") as fh:
        metadata = yaml.safe_load(fh)

    card = ModelCard.from_dict(metadata or {})
    errors = card.validate()
    if errors:
        for err in errors:
            click.echo(f"validation: {err}", err=True)
        if strict:
            click.echo("Card validation failed.", err=True)
            sys.exit(1)

    rendered = render_markdown(card) if out_format == "markdown" else export_json(card)
    out = Path(output_path)
    if out.suffix == ".json" and out_format == "markdown":
        click.echo("warning: .json extension with markdown format", err=True)
    out.write_text(rendered, encoding="utf-8")
    click.echo(f"Wrote {out_format} model card to {out}")


@main.command("validate")
@click.option("--input", "input_path", required=True, type=click.Path(exists=True),
              help="YAML metadata file to validate.")
def validate(input_path: str) -> None:
    """Validate metadata without rendering; exit 1 on errors."""
    with open(input_path, encoding="utf-8") as fh:
        metadata = yaml.safe_load(fh)
    try:
        ModelCard.from_dict(metadata or {}).ensure_valid()
    except CardValidationError as exc:
        click.echo(f"invalid: {exc}", err=True)
        sys.exit(1)
    click.echo("valid")


if __name__ == "__main__":
    main()
