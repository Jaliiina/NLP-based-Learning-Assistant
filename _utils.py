import os
import sys
import runpy
from pathlib import Path
from types import ModuleType
from typing import Optional

import streamlit as st


def root_dir() -> Path:
    return Path(__file__).resolve().parent


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_sys_path(path: Path) -> None:
    p = str(path)
    if p not in sys.path:
        sys.path.insert(0, p)


def load_module_from_path(module_name: str, file_path: Path) -> ModuleType:
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_streamlit_script(file_path: Path, working_dir: Optional[Path] = None) -> None:
    orig_set_page_config = st.set_page_config
    orig_sidebar = st.sidebar
    old_cwd = os.getcwd()
    try:
        st.set_page_config = lambda *args, **kwargs: None
        st.sidebar = st.container()
        if working_dir is not None:
            os.chdir(str(working_dir))
        runpy.run_path(str(file_path), run_name="__main__")
    finally:
        st.set_page_config = orig_set_page_config
        st.sidebar = orig_sidebar
        os.chdir(old_cwd)
