"""Trimmed behavior utility functions."""

from ._legacy import export_public_symbols, load_legacy_module

_module = load_legacy_module('utils/trimmed_behavior_utils.py')
globals().update(export_public_symbols(_module))

