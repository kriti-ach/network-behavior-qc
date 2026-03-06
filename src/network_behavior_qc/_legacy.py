"""Compatibility loader for legacy modules during refactor."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


LEGACY_ROOT = Path(__file__).resolve().parents[1] / 'network-behavior-qc'
if str(LEGACY_ROOT) not in sys.path:
    # Needed so legacy imports like "from utils..." keep working.
    sys.path.insert(0, str(LEGACY_ROOT))


def load_legacy_module(relative_path: str):
    module_path = LEGACY_ROOT / relative_path
    module_name = f'_legacy_{relative_path.replace("/", "_").replace(".py", "")}'
    spec = spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f'Could not load legacy module: {module_path}')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def export_public_symbols(module) -> dict:
    return {
        name: value
        for name, value in module.__dict__.items()
        if not name.startswith('_')
    }

