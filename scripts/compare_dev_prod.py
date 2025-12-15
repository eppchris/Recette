#!/usr/bin/env python3
import os
from pathlib import Path
from datetime import datetime

# === CHEMINS ===
DEV_ROOT = Path("/Users/christianepp/Documents/DEV/Recette")
PROD_ROOT = Path("/volume1/homes/admin/recette")


def is_excluded(rel_path: Path) -> bool:
    """
    Exclusions :
    - data/**
    - static/images/recipes/**
    """
    parts = rel_path.parts

    if not parts:
        return False

    if parts[0] == "data":
        return True

    if len(parts) >= 3 and parts[:3] == ("static", "images", "recipes"):
        return True

    return False


def is_modified(src: Path, dst: Path) -> bool:
    """
    Fichier considéré modifié si :
    - absent en prod
    - taille différente
    - date de modification plus récente en dev
    """
    if not dst.exists():
        return True

    src_stat = src.stat()
    dst_stat = dst.stat()

    if src_stat.st_size != dst_stat.st_size:
        return True

    if src_stat.st_mtime > dst_stat.st_mtime:
        return True

    return False


def list_modified_files(dev_root: Path, prod_root: Path):
    modified = []

    for root, _, files in os.walk(dev_root):
        root_path = Path(root)
        for file in files:
            src = root_path / file
            rel_path = src.relative_to(dev_root)

            if is_excluded(rel_path):
                continue

            dst = prod_root / rel_path

            if is_modified(src, dst):
                modified.append(rel_path)

    return modified


def main():
    print("=== COMPARAISON DEV → PROD (liste uniquement) ===")
    print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"DEV  : {DEV_ROOT}")
    print(f"PROD : {PROD_ROOT}\n")

    files = list_modified_files(DEV_ROOT, PROD_ROOT)

    if not files:
        print("✅ Aucun fichier modifié.")
        return

    print(f"📄 Fichiers modifiés ou nouveaux : {len(files)}\n")
    for f in sorted(files):
        print(f"- {f}")


if __name__ == "__main__":
    main()
