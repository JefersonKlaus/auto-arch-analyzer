import logging
import sys
from pathlib import Path
import builtins
import importlib.util
import inspect
import os

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Ensure `src/` is on sys.path so top-level packages like `lambdas` and `api` can be imported in tests.
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


_original_import = builtins.__import__


def _workspace_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Resolve bare imports like `from models import X` against the caller's directory.

    This is only used for workspace code under `src/` and falls back to the normal import
    machinery for everything else.
    """
    if level == 0 and "." not in name:
        caller_file = None
        frame = inspect.currentframe()
        try:
            frame = frame.f_back
            while frame:
                fn = frame.f_globals.get("__file__")
                if fn and str(Path(fn).resolve()).startswith(str(SRC_DIR.resolve())):
                    caller_file = Path(fn).resolve()
                    break
                frame = frame.f_back
        finally:
            del frame

        if caller_file:
            candidate = caller_file.parent / f"{name}.py"
            if candidate.exists():
                relative_parent = caller_file.parent.relative_to(SRC_DIR)
                qualified_name = ".".join((*relative_parent.parts, name))

                if qualified_name in sys.modules:
                    module = sys.modules[qualified_name]
                    sys.modules[name] = module
                    return module

                spec = importlib.util.spec_from_file_location(qualified_name, candidate)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[qualified_name] = module
                    sys.modules[name] = module
                    spec.loader.exec_module(module)
                    return module

    return _original_import(name, globals, locals, fromlist, level)


builtins.__import__ = _workspace_import


def _collect_dirs_with_py(root: Path):
    paths = []
    if not root.exists():
        return paths
    for dirpath, dirnames, filenames in os.walk(root):
        if any(f.endswith(".py") for f in filenames):
            paths.append(dirpath)
    # sort deterministic by depth then name
    paths.sort(key=lambda p: (p.count(os.sep), p))
    return paths


def add_package_subdirs_to_sys_path():
    # Collect lambdas dirs first, then api dirs to prefer lambdas' bare modules
    lambdas_root = SRC_DIR / "lambdas"
    api_root = SRC_DIR / "api"

    lambdas_paths = _collect_dirs_with_py(lambdas_root)
    api_paths = _collect_dirs_with_py(api_root)

    # Prepend lambdas_paths then api_paths to sys.path while avoiding duplicates
    new_paths = []
    for p in lambdas_paths + api_paths:
        if p not in new_paths:
            new_paths.append(p)

    # Insert them at the front preserving order: lambdas first then api
    for p in reversed(new_paths):
        if p not in sys.path:
            sys.path.insert(0, p)


add_package_subdirs_to_sys_path()
