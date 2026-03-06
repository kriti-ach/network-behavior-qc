"""Global constants."""

from ._legacy import export_public_symbols, load_legacy_module

_module = load_legacy_module('utils/globals.py')
globals().update(export_public_symbols(_module))

