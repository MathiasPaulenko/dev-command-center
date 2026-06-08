#!/usr/bin/env python3
"""Cross-platform build script for DevCommandCenter using PyInstaller."""

import platform
import subprocess
import sys
from pathlib import Path


def get_platform_suffix() -> str:
    system = platform.system().lower()
    if system == "windows":
        return ".exe"
    elif system == "darwin":
        return "-macos"
    elif system == "linux":
        return "-linux"
    return ""


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build() -> None:
    ensure_pyinstaller()

    root = Path(__file__).resolve().parent.parent
    main_script = root / "main.py"
    dist_dir = root / "dist"
    output_name = "DevCommandCenter"

    print(f"Building {output_name} for {platform.system()}...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", output_name,
        "--onefile",
        "--windowed",
        "--hidden-import", "sqlalchemy.ext.baked",
        "--hidden-import", "sqlalchemy.sql.default_comparator",
        str(main_script),
    ]

    subprocess.check_call(cmd, cwd=root)

    suffix = get_platform_suffix()
    src = dist_dir / (output_name + (".exe" if platform.system() == "Windows" else ""))
    dest = dist_dir / (output_name + suffix)

    if src.exists() and src != dest:
        src.rename(dest)
        print(f"Renamed to: {dest.name}")

    print(f"Build complete: {dest}")


if __name__ == "__main__":
    build()
