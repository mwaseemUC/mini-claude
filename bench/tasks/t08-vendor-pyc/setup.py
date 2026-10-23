"""Compile the private vendor source into a sourceless vendorlib.pyc in the workspace."""

import py_compile
from pathlib import Path


def setup(workspace: Path, task_dir: Path) -> None:
    src = Path(task_dir) / "private" / "vendorlib_src.py"
    py_compile.compile(str(src), cfile=str(Path(workspace) / "vendorlib.pyc"), doraise=True)
