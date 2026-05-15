"""
Generate synthetic columns for pandas — ints, floats, choices, weighted choices, names.

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
from data_generator.generator import legacy_sample_frame

__all__ = [
    "constant_column",
    "random_floats",
    "random_ints",
    "random_names",
    "random_values",
    "random_values_with_probs",
    "legacy_sample_frame",
]
__version__ = "0.2.0"
