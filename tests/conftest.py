import importlib.util
import sys
from pathlib import Path


def _load_dpw_from_src() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    init_py = src_dir / "__init__.py"
    if not init_py.exists():
        return

    spec = importlib.util.spec_from_file_location(
        "dpw",
        init_py,
        submodule_search_locations=[str(src_dir)],
    )
    if spec is None or spec.loader is None:
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules["dpw"] = module
    spec.loader.exec_module(module)


_load_dpw_from_src()
