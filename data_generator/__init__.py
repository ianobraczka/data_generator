"""
Generate synthetic pandas datasets from simple schemas — ints, floats, choices,
weighted choices, names, emails, booleans, and dates.

This package replaces the ad-hoc Colab script with importable, testable modules.
"""

from data_generator.distributions import (
    constant_column,
    random_floats,
    random_ints,
    random_names,
    random_values,
    random_values_with_probs,
)
from data_generator.fields import SUPPORTED_FIELD_TYPES, validate_field_spec, validate_schema
from data_generator.generator import generate_dataset, legacy_sample_frame

__all__ = [
    "SUPPORTED_FIELD_TYPES",
    "constant_column",
    "generate_dataset",
    "legacy_sample_frame",
    "random_floats",
    "random_ints",
    "random_names",
    "random_values",
    "random_values_with_probs",
    "validate_field_spec",
    "validate_schema",
]
__version__ = "0.2.0"
