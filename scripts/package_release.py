#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, shutil, zipfile

ROOT = Path(__file__).resolve().parents[1]

def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=(ROOT/"VERSION").read_text().strip())
    args = ap.parse_args()
    version = args.version.removeprefix("v")
    expected = (ROOT/"VERSION").read_text().strip()
    if version != expected:
        raise SystemExit(f"version mismatch: tag={version} VERSION={expected}")

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for p in dist.iterdir():
        if p.name != ".gitkeep":
            if p.is_file(): p.unlink()
            else: shutil.rmtree(p)

    name = f"codex-sol-luna-switchable-v{version}"
    archive = dist / f"{name}.zip"

    include_roots = [
        "README.md","README.en.md","LICENSE","NOTICE.md","CHANGELOG.md",
        "SECURITY.md","CONTRIBUTING.md","CODE_OF_CONDUCT.md","RELEASE_POLICY.md",
        "VERSION","agents","profiles","templates","docs","scripts","bin"
    ]
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for item in include_roots:
            p = ROOT / item
            if p.is_file():
                z.write(p, Path(name)/p.relative_to(ROOT))
            else:
                for f in p.rglob("*"):
                    if f.is_file():
                        z.write(f, Path(name)/f.relative_to(ROOT))

    sums = dist / "SHA256SUMS.txt"
    sums.write_text(f"{sha256(archive)}  {archive.name}\n", encoding="utf-8")
    print(archive)
    print(sums)

if __name__ == "__main__":
    main()
