#!/usr/bin/env python3
"""Контракт ppt-master, на который опирается preza: проверка после каждого слияния релиза upstream.

    python tools/preza_contract.py --check [--smoke]
    python tools/preza_contract.py --selftest

--check: файлы и папки, поля графиков и атрибуты в коде скриптов, флаги в --help, указатели
deck-house-rules, attribution_guard.py. --smoke: экспорт tools/fixture в PPTX (нужны пакеты
requirements.txt). Код выхода 1 — контракт нарушен; список нарушений печатается.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PM = REPO / "skills/ppt-master"
FILES = [
    "SKILL.md",
    "requirements.txt",
    "references/image-generator.md",
    "references/executor-base.md",
    "references/visual-review.md",
    "references/animations.md",
    "references/artifact-ownership.md",
    "workflows/generate-pptx.md",
    "workflows/profiles/quick-generate.md",
    "workflows/stages/visual-review.md",
    "workflows/stages/customize-animations.md",
    "workflows/stages/verify-charts.md",
    "workflows/stages/resume-execute.md",
    "templates/design_spec_reference.md",
    "scripts/project_manager.py",
    "scripts/svg_to_pptx.py",
    "scripts/svg_quality_checker.py",
    "scripts/finalize_svg.py",
    "scripts/update_spec.py",
    "scripts/animation_config.py",
    "scripts/powerpoint_video.py",
    "scripts/attribution_guard.py",
    "scripts/stamp_native_fallbacks.py",
    "scripts/total_md_split.py",
]
DIRS = ["templates/styles", "templates/layouts", "templates/charts", "templates/tables"]
CODE_TOKENS = [
    "legend_position",
    "data_labels",
    "label_position",
    "chart_area_fill",
    "data-pptx-bounds",
    "data-pptx-role",
]
FLAGS = {
    ("scripts/svg_to_pptx.py", "--help"): [
        "--quick-generate",
        "--native-charts-and-tables",
        "--with-notes",
    ],
    ("scripts/project_manager.py", "init", "--help"): ["--dir"],
}
POINTERS = ["SKILL.md", "references/image-generator.md", "references/executor-base.md"]
MARK, SKILL = "(deck-house-rules)", "preza:deck-house-rules"
IDENTITY = 78  # ppt-master: _require_official_distribution_identity


def static_problems(pm):
    problems = [f"нет файла {f}" for f in FILES if not (pm / f).is_file()]
    problems += [f"нет папки {d}" for d in DIRS if not (pm / d).is_dir()]
    code = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in (pm / "scripts").rglob("*.py")
    )
    problems += [f"в коде скриптов нет «{t}»" for t in CODE_TOKENS if t not in code]
    for rel in POINTERS:
        text = (pm / rel).read_text(encoding="utf-8") if (pm / rel).is_file() else ""
        if not any(MARK in line and SKILL in line for line in text.splitlines()):
            problems.append(f"нет указателя deck-house-rules в {rel}")
    return problems


def run(args, cwd):
    r = subprocess.run(
        [sys.executable, *args], cwd=cwd, capture_output=True, text=True, timeout=600
    )
    return r.returncode, r.stdout + r.stderr


def live_problems(pm):
    problems = []
    for (script, *rest), flags in FLAGS.items():
        code, out = run([script, *rest], pm)
        if code == IDENTITY:
            return [f"{script}: нарушена идентичность дистрибутива (код 78)"]
        problems += [
            f"{script} {' '.join(rest)}: нет флага {f}" for f in flags if f not in out
        ]
    code, out = run(["scripts/attribution_guard.py"], pm)
    if code:
        problems.append(f"attribution_guard.py: код {code}\n{out[-800:]}")
    return problems


def smoke_problems(pm):
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "fixture"
        shutil.copytree(REPO / "tools/fixture", project)
        steps = [
            [
                "scripts/svg_quality_checker.py",
                str(project),
                "--quick-generate",
                "--canonical-authoring",
                "--stage",
                "final",
                "--json",
            ],
            [
                "scripts/svg_to_pptx.py",
                str(project),
                "--quick-generate",
                "-o",
                str(project / "smoke.pptx"),
            ],
        ]
        for step in steps:
            code, out = run(step, pm)
            if code == IDENTITY:
                return ["smoke: нарушена идентичность дистрибутива (код 78)"]
            if code:
                return [f"smoke: {Path(step[0]).name} код {code}\n{out[-1500:]}"]
        from pptx import Presentation

        slides = len(Presentation(project / "smoke.pptx").slides)
        return [] if slides == 1 else [f"smoke: слайдов {slides}, ожидался 1"]


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        pm = Path(tmp)
        for f in FILES:
            (pm / f).parent.mkdir(parents=True, exist_ok=True)
            (pm / f).write_text("fixture", encoding="utf-8")
        for d in DIRS:
            (pm / d).mkdir(parents=True, exist_ok=True)
        (pm / "scripts/tokens.py").write_text("\n".join(CODE_TOKENS), encoding="utf-8")
        for rel in POINTERS:
            (pm / rel).write_text(
                f"# T\n\n> rule {MARK}: `{SKILL}`\n", encoding="utf-8"
            )
        assert static_problems(pm) == []
        (pm / POINTERS[1]).write_text(
            "# T\n\nmentions deck-house-rules only\n", encoding="utf-8"
        )
        (pm / FILES[-1]).unlink()
        found = static_problems(pm)
        assert len(found) == 2 and "image-generator" in found[1], found
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        sys.exit()
    if not a.check:
        ap.error("нужен --check или --selftest")
    problems = (
        static_problems(PM)
        or live_problems(PM)
        or (smoke_problems(PM) if a.smoke else [])
    )
    for p in problems:
        print("✗", p)
    print("контракт preza: " + ("нарушен" if problems else "OK"))
    sys.exit(1 if problems else 0)
