# -*- mode: python ; coding: utf-8 -*-
"""Build two one-file executables (CLI + GUI). Run from repo root:
    uv sync --group dev && uv run pyinstaller medical-coder-llm-bundle.spec

    GitHub releases use this spec twice on macOS: Apple Silicon (macos-latest)
    and Intel x86_64 (macos-15-intel). EXE targets use native arch (target_arch None).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

ROOT = Path(SPEC).resolve().parent
SRC = ROOT / "src"

block_cipher = None

datas: list[tuple[str, str]] = []
datas += collect_data_files("medical_coder_llm.web")
datas += collect_data_files("medical_coder_llm.ontology")
datas += collect_data_files("certifi")
datas += copy_metadata("certifi")

hiddenimports = [
    "medical_coder_llm.web.app",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "starlette.staticfiles",
    "anyio._backends._asyncio",
]

if sys.platform != "win32":
    hiddenimports += ["uvloop", "httptools"]


def _analysis(entry: str) -> Analysis:
    return Analysis(
        [str(SRC / entry)],
        pathex=[str(SRC)],
        binaries=[],
        datas=list(datas),
        hiddenimports=list(hiddenimports),
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
        optimize=0,
    )


a_cli = _analysis("medical_coder_llm/cli.py")
pyz_cli = PYZ(a_cli.pure)
exe_cli = EXE(
    pyz_cli,
    a_cli.scripts,
    a_cli.binaries,
    a_cli.datas,
    [],
    name="medical-coder-llm",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

a_web = _analysis("medical_coder_llm/web/main.py")
pyz_web = PYZ(a_web.pure)
exe_web = EXE(
    pyz_web,
    a_web.scripts,
    a_web.binaries,
    a_web.datas,
    [],
    name="medical-coder-llm-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
