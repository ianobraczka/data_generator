"""
Generate synthetic pandas datasets from simple schemas — ints, floats, choices,
weighted choices, names, emails, booleans, and dates.

This package replaces the ad-hoc Colab script with importable, testable modules.
"""

from data_generator.ai_providers import ProviderError, get_provider
from data_generator.ai_schema import AISchemaError, generate_schema_from_prompt, save_schema_yaml
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
    "AISchemaError",
    "ProviderError",
    "SUPPORTED_FIELD_TYPES",
    "get_provider",
    "constant_column",
    "generate_dataset",
    "generate_schema_from_prompt",
    "legacy_sample_frame",
    "random_floats",
    "random_ints",
    "random_names",
    "random_values",
    "random_values_with_probs",
    "save_schema_yaml",
    "validate_field_spec",
    "validate_schema",
]
__version__ = "0.5.0"
