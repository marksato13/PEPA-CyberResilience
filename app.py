"""Cloud entrypoint for PEPA CyberResilience.

This file lets Streamlit Community Cloud or similar platforms start the app
from the repository root. On first boot it prepares the expected ~/bigdata
runtime layout and generates the Parquet dataset if it is missing.
"""
from pathlib import Path
import os
import runpy
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
BIGDATA_HOME = HOME / "bigdata"
PARQUET = BIGDATA_HOME / "output" / "cybersecurity_joined"


def copy_tree_contents(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        return
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def prepare_runtime() -> None:
    (BIGDATA_HOME / "scripts").mkdir(parents=True, exist_ok=True)
    (BIGDATA_HOME / "tablas").mkdir(parents=True, exist_ok=True)
    (BIGDATA_HOME / "output").mkdir(parents=True, exist_ok=True)
    (BIGDATA_HOME / "logs").mkdir(parents=True, exist_ok=True)
    copy_tree_contents(ROOT / "scripts", BIGDATA_HOME / "scripts")
    copy_tree_contents(ROOT / "tablas", BIGDATA_HOME / "tablas")


def ensure_parquet() -> None:
    if PARQUET.exists():
        return
    env = os.environ.copy()
    env.setdefault("JAVA_HOME", "/usr/lib/jvm/java-17-openjdk-amd64")
    env.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    subprocess.run(
        [sys.executable, str(BIGDATA_HOME / "scripts" / "pipeline_linux.py")],
        cwd=str(BIGDATA_HOME),
        env=env,
        check=True,
    )


prepare_runtime()
ensure_parquet()
runpy.run_path(str(BIGDATA_HOME / "scripts" / "dashboard.py"), run_name="__main__")
