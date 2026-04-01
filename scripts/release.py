#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

from release_support import (
    ensure_clean_worktree,
    ensure_release_branch,
    read_project_version,
    validate_changelog,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
DEFAULT_TWINE_CONFIG = Path.home() / ".pypirc-pubify-mpl"


def _print_step(index: int, message: str) -> None:
    print(f"[{index}] {message}")


def _run(cmd: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    print(f"+ {' '.join(shlex.quote(part) for part in cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=True, text=True)


def _capture(cmd: list[str], *, cwd: Path = REPO_ROOT) -> str:
    result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _git_status() -> str:
    return _capture(["git", "status", "--porcelain"])


def _git_branch() -> str:
    return _capture(["git", "branch", "--show-current"])


def _tag_exists(tag_name: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag_name}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _build_artifacts(version: str) -> list[Path]:
    out_dir = Path(tempfile.mkdtemp(prefix=f"pubify_release_{version.replace('.', '_')}_"))
    _run(
        [
            sys.executable,
            "-m",
            "build",
            "--sdist",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(out_dir),
        ]
    )
    artifacts = sorted(out_dir.glob(f"pubify_mpl-{version}*"))
    if not artifacts:
        raise RuntimeError(f"No build artifacts were produced for version {version}.")
    return artifacts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full pubify-mpl release flow.")
    parser.add_argument(
        "--config-file",
        type=Path,
        default=DEFAULT_TWINE_CONFIG,
        help="Path to the Twine config file to use for upload.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    version = read_project_version(PYPROJECT_PATH)
    tag_name = f"v{version}"

    _print_step(1, f"Validating release prerequisites for {version}")
    ensure_release_branch(_git_branch())
    ensure_clean_worktree(_git_status(), context="before release")
    validate_changelog(CHANGELOG_PATH, version)
    if _tag_exists(tag_name):
        raise ValueError(f"Git tag '{tag_name}' already exists.")
    if not args.config_file.exists():
        raise FileNotFoundError(f"Missing Twine config file: {args.config_file}")

    _print_step(2, "Running full test suite")
    _run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"])

    _print_step(3, "Running pre-commit hook")
    _run(["sh", ".githooks/pre-commit"])

    _print_step(4, "Re-checking worktree after pre-commit")
    ensure_clean_worktree(_git_status(), context="after pre-commit")

    _print_step(5, "Building fresh distribution artifacts")
    artifacts = _build_artifacts(version)

    _print_step(6, "Running twine check")
    _run([sys.executable, "-m", "twine", "check", *(str(path) for path in artifacts)])

    _print_step(7, f"Creating git tag {tag_name}")
    _run(["git", "tag", tag_name])

    _print_step(8, "Pushing main")
    _run(["git", "push", "origin", "main"])

    _print_step(9, f"Pushing tag {tag_name}")
    _run(["git", "push", "origin", tag_name])

    _print_step(10, "Uploading artifacts to PyPI")
    _run(
        [
            sys.executable,
            "-m",
            "twine",
            "upload",
            "--config-file",
            str(args.config_file),
            *(str(path) for path in artifacts),
        ]
    )

    print("Release complete.")
    for artifact in artifacts:
        print(f"- {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
