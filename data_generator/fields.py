"""
Field types supported by schema-driven generation (phase 2 wires validation and dispatch).

Each field spec is a dict with at least ``{"type": "<type_name>"}``.
"""

from __future__ import annotations

SUPPORTED_FIELD_TYPES: frozenset[str] = frozenset(
    {
        "int",
        "float",
        "choice",
        "weighted_choice",
        "name",
        "email",
        "boolean",
        "date",
    }
)
