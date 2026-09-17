"""Render model cards to Markdown (human-readable) and JSON (machine-readable)."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .schema import ModelCard

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=False)


def render_markdown(card: ModelCard) -> str:
    """Render the card through the bundled Jinja2 Markdown template."""
    card.ensure_valid()
    template = _env.get_template("card.md.j2")
    return template.render(card=card)


def export_json(card: ModelCard, *, indent: int = 2) -> str:
    """Export the card as machine-readable JSON for governance tooling."""
    card.ensure_valid()
    return json.dumps(card.to_dict(), indent=indent, default=str)
