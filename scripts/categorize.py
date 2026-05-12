#!/usr/bin/env python3
"""
Auto-categorize skills into folders based on SKILL.md content.

Scans the skills root directory for skill directories (containing SKILL.md
with YAML frontmatter) that are NOT already inside a recognized category folder.
Moves them into the best-matching category and regenerates README files.

Usage:
    python scripts/categorize.py                    # Scan and auto-categorize
    python scripts/categorize.py --dry-run          # Preview only, no moves
    python scripts/categorize.py --check            # Exit 1 if uncategorized skills exist
    python scripts/categorize.py --force reindex    # Regenerate READMEs only (no moves)
"""

import os
import sys
import re
import shutil
import argparse
from pathlib import Path

# --- Configuration ---

SKILLS_ROOT = Path(__file__).resolve().parent.parent

CATEGORY_DIRS = {
    "ui-design",
    "office-suite",
    "writing",
    "dev-workflow",
    "tools",
    "_uncategorized",
}

IGNORED_DIRS = {
    "scripts",
    "node_modules",
    "__pycache__",
    ".git",
    ".github",
    "_uncategorized",
}

CATEGORIES = {
    "ui-design": {
        "display": "UI设计",
        "description": "视觉设计、品牌标识、UI组件、设计系统。",
        "keywords": {
            "banner": 5, "brand": 5, "design": 3, "designer": 3, "ui": 3, "ux": 3,
            "component": 3, "tailwind": 5, "shadcn": 5, "css": 3, "radix": 4,
            "typography": 3, "color": 3, "logo": 5, "icon": 5, "svg": 4,
            "presentation": 2, "slide": 2, "chart": 2, "slideshow": 2,
            "visual identity": 5, "style guide": 4, "design system": 4, "design token": 4,
            "mockup": 3, "cip": 5, "token": 4, "font": 3, "palette": 4,
            "glassmorphism": 5, "minimalism": 4, "brutalism": 4, "neumorphism": 4,
            "dark mode": 4, "responsive": 3, "canvas": 3, "hero": 3,
            "social media": 3, "instagram": 4, "facebook": 4, "twitter": 4,
            "landing page": 4, "dashboard": 3, "e-commerce": 3, "saas": 3,
            "accessibility": 2, "animation": 2, "layout": 2,
        },
        "name_patterns": [
            "ckm:banner", "ckm:brand", "ckm:design", "ckm:ui",
            "ckm:slides", "ui-ux", "ui/ux",
        ],
    },
    "office-suite": {
        "display": "办公套装",
        "description": "文档处理：Word、PDF、PowerPoint、Excel。",
        "keywords": {
            "docx": 5, ".docx": 5, "word document": 5, "word": 3,
            "pdf": 5, ".pdf": 5, "pptx": 5, ".pptx": 5, "powerpoint": 5,
            "xlsx": 5, ".xlsx": 5, ".csv": 4, "excel": 5, "spreadsheet": 5,
            "merge": 2, "split": 2, "ocr": 3, "form": 3, "fillable": 3,
            "watermark": 3, "encrypt": 3, "decrypt": 3, "rotate": 3,
            "tracked change": 4, "comment": 3, "letterhead": 4,
            "table of contents": 4, "heading": 2, "page number": 4,
            "report": 2, "memo": 3, "template": 2, "letter": 3,
            "openpyxl": 5, "pandas": 2, "reportlab": 4, "pypdf": 4,
            "libreoffice": 4, "pandoc": 3, "formula": 2, "financial model": 4,
        },
        "name_patterns": ["docx", "pdf", "pptx", "xlsx"],
    },
    "writing": {
        "display": "写作套装",
        "description": "写作辅助与中文文本编辑。",
        "keywords": {
            "writing": 3, "write": 2, "documentation": 3, "proposal": 3,
            "spec": 2, "technical spec": 4, "draft": 3, "author": 2,
            "editing": 3, "edit": 2, "refine": 2, "text": 2,
            "ai writing": 4, "ai 写作": 5, "humanizer": 5, "人性化": 5,
            "co-author": 5, "coauthor": 5, "co-authoring": 5, "协作": 4,
            "reader test": 4, "proofread": 3, "review": 2,
            "去除": 4, "痕迹": 4, "自然": 2, "中文": 3,
            "decision doc": 4, "rfc": 3, "prd": 2,
        },
        "name_patterns": ["doc-coauthoring", "humanizer"],
    },
    "dev-workflow": {
        "display": "开发流程",
        "description": "规划、架构评审、TDD、Issue管理。",
        "keywords": {
            "architecture": 4, "refactor": 3, "codebase": 3,
            "tdd": 5, "test-driven": 5, "test first": 4, "red-green": 5,
            "issue": 3, "ticket": 3, "tracker": 3,
            "prd": 4, "specification": 3, "requirement": 2,
            "grill": 5, "interview": 3, "stress-test": 4, "stress test": 4,
            "plan": 2, "design decision": 3, "decision tree": 3,
            "deepen": 4, "deep module": 4, "module": 2, "seam": 3,
            "adr": 4, "context.md": 4, "domain": 2, "glossary": 2,
            "interface": 2, "implementation": 2,
            "tracer bullet": 4, "vertical slice": 4,
            "implementation": 2, "locality": 3, "leverage": 3,
        },
        "name_patterns": [
            "grill", "tdd", "to-issues", "to-prd",
            "improve-codebase", "improve-codebase-architecture",
        ],
    },
    "tools": {
        "display": "工具与自动化",
        "description": "技能发现、浏览器自动化、技能创建。",
        "keywords": {
            "skill": 3, "skills": 3, "install skill": 4, "discover": 3,
            "browser": 4, "playwright": 5, "automation": 3, "test": 2,
            "screenshot": 4, "snapshot": 4, "headless": 3, "headed": 3,
            "eval": 3, "benchmark": 2, "evaluation": 3, "assertion": 2,
            "package": 2, "create skill": 4, "modify skill": 4,
            "cli": 2, "npx": 3, "npm": 2, "install": 2,
            "trigger": 2, "triggering": 3, "description optimization": 3,
        },
        "name_patterns": ["find-skills", "playwright", "skill-creator"],
    },
}

# Minimum score threshold to assign to a category
SCORE_THRESHOLD = 10

# Category directory names
CATEGORY_DIR_NAMES = set(CATEGORIES.keys())

# --- YAML parsing (simple, no PyYAML dependency) ---

def parse_frontmatter(filepath: Path):
    """Parse YAML frontmatter from a SKILL.md file. Returns (name, description) or (None, None)."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return None, None

    # Match YAML frontmatter between --- delimiters
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return None, None

    frontmatter = m.group(1)
    name_match = re.search(r'^name:\s*(.*?)$', frontmatter, re.MULTILINE)
    desc_match = re.search(r'^description:\s*(.*?)$', frontmatter, re.MULTILINE)

    name = name_match.group(1).strip().strip('"').strip("'") if name_match else None
    description = desc_match.group(1).strip().strip('"').strip("'") if desc_match else None

    # Handle multi-line descriptions (YAML literal block scalar with |)
    if desc_match and not description:
        desc_match = re.search(r'^description:\s*\|?\s*\n(.*?)(?=\n\w+:|$)', frontmatter, re.MULTILINE | re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()

    return name, description


# --- Classification ---

def classify_skill(name: str, description: str):
    """Classify a skill by scoring against category profiles. Returns (category, score)."""
    if not name and not description:
        return ("_uncategorized", 0)

    name_lower = (name or "").lower()
    desc_lower = (description or "").lower()

    best_category = "_uncategorized"
    best_score = 0
    scores = {}

    for cat_name, cat_config in CATEGORIES.items():
        score = 0

        # Score from keyword matches in description
        for keyword, weight in cat_config["keywords"].items():
            if keyword in desc_lower:
                score += weight

        # Bonus from name pattern matches
        for pattern in cat_config["name_patterns"]:
            if pattern.lower() == name_lower:
                score += 15  # Exact match
            elif pattern.lower() in name_lower:
                score += 10  # Substring match

        scores[cat_name] = score
        if score > best_score:
            best_score = score
            best_category = cat_name

    if best_score < SCORE_THRESHOLD:
        return ("_uncategorized", best_score)

    return (best_category, best_score)


# --- Directory scanning ---

def find_skills(at_root: bool = True):
    """Find all skill directories (containing SKILL.md).
    If at_root=True, only scan top-level (uncategorized).
    If at_root=False, scan recursively for README generation."""
    skills = []
    root = SKILLS_ROOT

    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        if entry.name in IGNORED_DIRS:
            continue
        if entry.name in CATEGORY_DIR_NAMES:
            # It's a category folder - recurse into it
            for sub in sorted(entry.iterdir()):
                if sub.is_dir() and not sub.name.startswith("."):
                    skill_md = sub / "SKILL.md"
                    if skill_md.exists():
                        skills.append((sub, entry.name))
            continue

        # Top-level skill directory
        skill_md = entry / "SKILL.md"
        if skill_md.exists():
            skills.append((entry, None))

    return skills


def find_uncategorized():
    """Find skills in the root directory (not yet in a category folder)."""
    skills = []
    root = SKILLS_ROOT
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        if entry.name in IGNORED_DIRS:
            continue
        if entry.name in CATEGORY_DIR_NAMES:
            continue
        skill_md = entry / "SKILL.md"
        if skill_md.exists():
            skills.append(entry)
    return skills


# --- README generation ---

def generate_main_readme():
    """Generate skills/README.md with the master index."""
    lines = [
        "# Claude Code 技能仓库",
        "",
        "按用途分类管理所有技能，帮助 Agent 快速找到合适的工具。",
        "",
        "## 分类总览",
        "",
        "| 分类 | 技能数 | 说明 |",
        "|------|--------|------|",
    ]

    for cat_name in ["ui-design", "office-suite", "writing", "dev-workflow", "tools"]:
        cat = CATEGORIES[cat_name]
        cat_path = SKILLS_ROOT / cat_name
        count = sum(
            1 for d in cat_path.iterdir()
            if d.is_dir() and not d.name.startswith(".") and (d / "SKILL.md").exists()
        )
        lines.append(
            f"| [{cat['display']}]({cat_name}/README.md) | {count} | {cat['description']} |"
        )

    lines.extend([
        "",
        "## 运作机制",
        "",
        "- 每个分类文件夹包含用途相近的技能，方便 Agent 按需检索。",
        "- 新技能放入 `skills/` 根目录后，下次启动 Claude Code 时会自动归类到对应文件夹。",
        "- 无法自动归类的技能会被放入 `_uncategorized/`，等待人工审核。",
        "- 手动运行 `python scripts/categorize.py` 可立即触发归类。",
        "",
        "## 快速查找",
        "",
        "| 需求 | 去这里 |",
        "|------|--------|",
        "| 设计UI、Banner、Logo 或品牌 | [UI设计](ui-design/README.md) |",
        "| 创建或编辑 Word/PDF/PPT/Excel 文件 | [办公套装](office-suite/README.md) |",
        "| 写作文档、去除AI写作痕迹 | [写作套装](writing/README.md) |",
        "| 架构规划、TDD、创建Issue/PRD | [开发流程](dev-workflow/README.md) |",
        "| 浏览器自动化、发现/创建技能 | [工具与自动化](tools/README.md) |",
        "",
        "---",
        "*由 `scripts/categorize.py` 自动生成*",
    ])

    (SKILLS_ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_category_readme(cat_name: str):
    """Generate a README.md for a category folder."""
    cat = CATEGORIES[cat_name]
    cat_path = SKILLS_ROOT / cat_name

    skills = []
    for d in sorted(cat_path.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            skill_md = d / "SKILL.md"
            if skill_md.exists():
                name, desc = parse_frontmatter(skill_md)
                display_name = name or d.name
                short_desc = desc[:100] + "..." if desc and len(desc) > 100 else (desc or "")
                skills.append((d.name, display_name, short_desc))

    lines = [
        f"# {cat['display']}（{len(skills)}个技能）",
        "",
        cat["description"],
        "",
        "## 技能列表",
        "",
        "| 技能 | 用途 |",
        "|------|------|",
    ]

    for dirname, display_name, desc in skills:
        lines.append(f"| [{display_name}]({dirname}/) | {desc} |")

    lines.extend([
        "",
        "## 相关分类",
        "",
    ])

    other_cats = [c for c in ["ui-design", "office-suite", "writing", "dev-workflow", "tools"] if c != cat_name]
    for other in other_cats:
        oc = CATEGORIES[other]
        lines.append(f"- [{oc['display']}](../{other}/README.md) — {oc['description']}")

    lines.extend([
        "",
        "---",
        "*由 `scripts/categorize.py` 自动生成*",
    ])

    (cat_path / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_uncategorized_readme():
    """Generate README for _uncategorized folder."""
    lines = [
        "# 未归类技能",
        "",
        "这里的技能无法被自动归类，需要人工审核。",
        "",
        "## 处理步骤",
        "",
        "1. 检查技能的 SKILL.md 描述是否清晰表达了技能的用途。",
        "2. 更新描述，加入与其用途相关的关键词。",
        "3. 运行 `python scripts/categorize.py` 重新归类。",
        "4. 如果技能确实无法归入现有分类，考虑创建新的分类文件夹。",
        "",
        "---",
        "*由 `scripts/categorize.py` 自动生成*",
    ]
    (_uncategorized := SKILLS_ROOT / "_uncategorized" / "README.md")
    (SKILLS_ROOT / "_uncategorized" / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_all_readmes():
    """Regenerate all README.md files."""
    generate_main_readme()
    for cat_name in CATEGORY_DIR_NAMES:
        generate_category_readme(cat_name)
    generate_uncategorized_readme()
    print("  README files regenerated.")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Auto-categorize skills into folders")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no moves")
    parser.add_argument("--check", action="store_true", help="Exit 1 if uncategorized skills exist")
    parser.add_argument("--force", choices=["reindex"], help="Regenerate READMEs only")
    args = parser.parse_args()

    os.chdir(str(SKILLS_ROOT))

    if args.force == "reindex":
        print("Regenerating README files...")
        generate_all_readmes()
        return

    if args.check:
        uncategorized = find_uncategorized()
        if uncategorized:
            print(f"WARNING: {len(uncategorized)} uncategorized skill(s):")
            for d in uncategorized:
                print(f"  - {d.name}")
            sys.exit(1)
        print("All skills are categorized.")
        return

    uncategorized = find_uncategorized()

    if not uncategorized:
        print("No uncategorized skills found. Regenerating READMEs...")
        generate_all_readmes()
        return

    print(f"Found {len(uncategorized)} uncategorized skill(s).\n")

    moves = []
    for skill_dir in uncategorized:
        skill_md = skill_dir / "SKILL.md"
        name, description = parse_frontmatter(skill_md)
        category, score = classify_skill(name, description)

        print(f"  {skill_dir.name}:")
        print(f"    name: {name or '(none)'}")
        print(f"    desc: {(description or '(none)')[:80]}...")
        print(f"    -> {category} (score: {score})")

        moves.append((skill_dir, category))

    if args.dry_run:
        print(f"\n[DRY RUN] Would move {len(moves)} skills. No changes made.")
        return

    print(f"\nMoving {len(moves)} skills...")
    for skill_dir, category in moves:
        dest = SKILLS_ROOT / category / skill_dir.name
        if dest.exists():
            print(f"  SKIP {skill_dir.name}: destination already exists")
            continue
        shutil.move(str(skill_dir), str(dest))
        print(f"  MOVED {skill_dir.name} -> {category}/")

    print("\nRegenerating README files...")
    generate_all_readmes()
    print("\nDone.")


if __name__ == "__main__":
    main()
