"""Config module."""

from ._legacy import export_public_symbols, load_legacy_module

_module = load_legacy_module('utils/config.py')
globals().update(export_public_symbols(_module))

