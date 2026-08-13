"""
Spectra Release Automation Script (Phase 10).

Executes end-to-end release pipeline:
  1. Runs backend unit and fault recovery test suites.
  2. Runs benchmark suite (if backend is active).
  3. Builds desktop frontend static bundle (vite build / tsc).
  4. Attempts Tauri application build packaging (if rust/tauri toolchain present).
  5. Assembles release bundle artifacts into dist_release/v1.0.0/

Usage:
  python scripts/release.py --version 1.0.0
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def log(msg: str):
    print(f"\n[RELEASE] {msg}")


def run_cmd(cmd: list[str], cwd: Path) -> bool:
    log(f"Running command: {' '.join(cmd)} (in {cwd.name})")
    res = subprocess.run(cmd, cwd=cwd, text=True)
    if res.returncode != 0:
        print(f"FAILED: Command returned exit code {res.returncode}")
        return False
    return True


def step_run_tests() -> bool:
    log("Step 1: Running Backend Unit & Fault Recovery Tests")
    api_dir = ROOT_DIR / "apps" / "api"
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    return run_cmd(cmd, cwd=api_dir)


def step_run_benchmarks() -> bool:
    log("Step 2: Running Benchmark Suite")
    bm_script = ROOT_DIR / "scripts" / "benchmark_runner.py"
    cmd = [sys.executable, str(bm_script), "--output", str(ROOT_DIR / "benchmarks" / "report.json")]
    res = subprocess.run(cmd, cwd=ROOT_DIR, text=True)
    if res.returncode != 0:
        log("Warning: Benchmark step did not complete (backend may be offline). Proceeding...")
    return True


def step_build_frontend() -> bool:
    log("Step 3: Building Desktop Frontend Bundle")
    desktop_dir = ROOT_DIR / "apps" / "desktop"
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    cmd = [npm_cmd, "run", "build"]
    return run_cmd(cmd, cwd=desktop_dir)


def step_package_tauri() -> bool:
    log("Step 4: Packaging Tauri Application")
    desktop_dir = ROOT_DIR / "apps" / "desktop"
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    # Check if cargo / rust is available
    if not shutil.which("cargo"):
        log("Note: Rust/Cargo toolchain not found in PATH. Skipping binary compilation.")
        log("To build native installer manually later: cd apps/desktop && npm run tauri build")
        return True

    cmd = [npm_cmd, "run", "tauri", "build"]
    return run_cmd(cmd, cwd=desktop_dir)


def step_assemble_artifacts(version: str) -> bool:
    log("Step 5: Assembling Release Bundle Artifacts")
    release_dir = ROOT_DIR / "dist_release" / f"v{version}"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "app_name": "Spectra",
        "version": version,
        "release_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase": "10-polish",
        "artifacts": [],
    }

    # Copy docs
    docs_target = release_dir / "docs"
    shutil.copytree(ROOT_DIR / "docs", docs_target)
    manifest["artifacts"].append("docs/")

    # Copy benchmarks report if available
    report_file = ROOT_DIR / "benchmarks" / "report.json"
    if report_file.exists():
        shutil.copy(report_file, release_dir / "benchmark_report.json")
        manifest["artifacts"].append("benchmark_report.json")

    # Copy frontend dist build
    frontend_dist = ROOT_DIR / "apps" / "desktop" / "dist"
    if frontend_dist.exists():
        shutil.copytree(frontend_dist, release_dir / "frontend_dist")
        manifest["artifacts"].append("frontend_dist/")

    # Check Tauri bundle outputs
    bundle_dir = ROOT_DIR / "apps" / "desktop" / "src-tauri" / "target" / "release" / "bundle"
    if bundle_dir.exists():
        shutil.copytree(bundle_dir, release_dir / "tauri_bundles")
        manifest["artifacts"].append("tauri_bundles/")

    # Save release manifest
    manifest_path = release_dir / "release_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    log(f"SUCCESS: Release v{version} assembled at: {release_dir.resolve()}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Spectra Release Automation")
    parser.add_argument("--version", default="1.0.0")
    args = parser.parse_args()

    print(f"=== SPECTRA RELEASE PIPELINE v{args.version} ===")

    if not step_run_tests():
        sys.exit(1)

    step_run_benchmarks()

    if not step_build_frontend():
        sys.exit(1)

    step_package_tauri()

    if not step_assemble_artifacts(args.version):
        sys.exit(1)

    print("\n=== RELEASE PIPELINE COMPLETE SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
