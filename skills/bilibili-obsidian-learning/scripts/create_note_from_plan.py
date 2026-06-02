import argparse
import json
import shutil
from pathlib import Path


def copy_tree_files(src_dir, dst_dir):
    src = Path(src_dir)
    dst = Path(dst_dir)
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for path in src.rglob("*"):
        if path.is_file():
            rel = path.relative_to(src)
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst / rel)


def yaml_scalar(value):
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def main():
    parser = argparse.ArgumentParser(description="Create a three-part Obsidian video learning note from a JSON plan.")
    parser.add_argument("plan_json")
    parser.add_argument("vault_dir")
    parser.add_argument("--domain", default=None)
    args = parser.parse_args()

    plan = json.loads(Path(args.plan_json).read_text(encoding="utf-8"))
    title = plan["title"]
    domain = args.domain or plan.get("learning_domain") or "课程/AI工具"
    rel_dir = Path(*domain.replace("\\", "/").split("/")) / title
    target_dir = Path(args.vault_dir) / rel_dir
    assets_dir = target_dir / "assets" / "selected"
    transcript_dir = target_dir / "transcript"
    target_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir.mkdir(parents=True, exist_ok=True)

    if plan.get("assets_dir"):
        copy_tree_files(plan["assets_dir"], assets_dir)
    if plan.get("transcript_dir"):
        copy_tree_files(plan["transcript_dir"], transcript_dir)

    lines = ["---"]
    for key in [
        "type",
        "source_platform",
        "source_url",
        "bvid",
        "title",
        "author",
        "published",
        "created",
        "learning_domain",
        "status",
    ]:
        value = plan.get(key)
        if value is not None:
            lines.append(f"{key}: {yaml_scalar(value)}")
    tags = plan.get("tags") or []
    if tags:
        lines.append("tags:")
        lines.extend(f"  - {tag}" for tag in tags)
    lines.extend(["---", "", f"# {title}", ""])

    opening = plan.get("opening", {})
    lines.extend(["## 00. 开篇说明", "", "### 学习大纲", ""])
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(opening.get("outline", []), 1))
    lines.extend(["", "### 学完后的预期效果", ""])
    lines.extend(f"- {item}" for item in opening.get("outcomes", []))
    lines.extend(["", "### 工具与产物", ""])
    lines.extend(f"- {item}" for item in opening.get("tools", []))
    if opening.get("mermaid"):
        lines.extend(["", "### 全局框架", "", "```mermaid", opening["mermaid"], "```"])

    lines.extend(["", "## 01. 课程主体", ""])
    for idx, section in enumerate(plan.get("sections", []), 1):
        lines.extend([
            f"### {idx}. {section['title']}",
            "",
            f"**时间段**：`{section.get('time', '')}`",
            "",
        ])
        if section.get("image"):
            lines.extend([f"![[assets/selected/{section['image']}]]", ""])
        lines.extend(["**本段核心观点**", "", f"- {section.get('summary', '')}", "", "**知识框架**", ""])
        lines.extend(f"- {point}" for point in section.get("points", []))
        lines.extend(["", "**可迁移用法**", ""])
        lines.extend(f"- {item}" for item in section.get("transfer", []))
        lines.extend(["", "---", ""])

    reflection = plan.get("reflection", {})
    lines.extend(["## 02. 总结与反思", "", "### 全片知识框架", ""])
    lines.extend(f"- {item}" for item in reflection.get("framework", []))
    lines.extend(["", "### 关键结论", ""])
    lines.extend(f"- {item}" for item in reflection.get("conclusions", []))
    lines.extend(["", "### 思考题", ""])
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(reflection.get("questions", []), 1))
    lines.extend(["", "### 泛化能力延伸", ""])
    lines.extend(f"- {item}" for item in reflection.get("extensions", []))
    lines.extend(["", "### 下一步行动", ""])
    lines.extend(f"- [ ] {item}" for item in reflection.get("actions", []))

    if plan.get("appendix"):
        lines.extend(["", "## 03. 附录", ""])
        lines.extend(f"- {item}" for item in plan["appendix"])

    note_path = target_dir / f"{title}.md"
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(note_path)


if __name__ == "__main__":
    main()
