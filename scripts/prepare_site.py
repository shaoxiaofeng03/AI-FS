#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prepare_site.py —— 构建 VitePress 前，把运行期文件复制到 public/。

复制内容：
  tracker/index.html      -> public/tracker/index.html
  plan/plan.json          -> public/plan/plan.json
  data/checkins.json      -> public/data/checkins.json
  assets/tracker-preview.png -> public/assets/tracker-preview.png
  checkin/W*.md           -> public/checkin/W*.md（并生成 index.html 下载页）

用法：
  python3 scripts/prepare_site.py
  python3 scripts/prepare_site.py --check   # 只检查源文件是否存在
"""

from __future__ import annotations

import argparse
import html
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

COPIES = [
    (ROOT / "tracker" / "index.html", PUBLIC / "tracker" / "index.html"),
    (ROOT / "plan" / "plan.json", PUBLIC / "plan" / "plan.json"),
    (ROOT / "data" / "checkins.json", PUBLIC / "data" / "checkins.json"),
    (ROOT / "assets" / "tracker-preview.png", PUBLIC / "assets" / "tracker-preview.png"),
]


def copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise SystemExit(f"缺少源文件：{src}\n提示：先运行 python3 scripts/build_tracker.py，并确认 data/checkins.json 存在。")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_checkins() -> int:
    src_dir = ROOT / "checkin"
    dst_dir = PUBLIC / "checkin"
    files = sorted(p for p in src_dir.glob("W*.md") if p.is_file())
    if not files:
        return 0
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in files:
        shutil.copy2(src, dst_dir / src.name)

    items = []
    for src in files:
        name = src.name
        items.append(
            f'<li><a href="./{html.escape(name)}">{html.escape(name)}</a></li>'
        )
    index = f"""<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>每周打卡文件 · AI 全栈 22 周</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", sans-serif;
         max-width: 760px; margin: 40px auto; padding: 0 20px; color: #1f2937; line-height: 1.7; }}
  h1 {{ font-size: 24px; }}
  a {{ color: #4f46e5; }}
  li {{ margin: 6px 0; }}
  .tip {{ background: #eef2ff; border: 1px solid #c7d2fe; padding: 12px 14px; border-radius: 10px; }}
</style>
<h1>每周打卡文件</h1>
<p class="tip">这些是 Markdown 文件，点击会显示原文；建议下载后用编辑器/笔记软件打开。
回到 <a href="../tracker/">打卡看板</a>。</p>
<ul>
{''.join(items)}
</ul>
</html>
"""
    (dst_dir / "index.html").write_text(index, encoding="utf-8")
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="复制 VitePress public 资源")
    parser.add_argument("--check", action="store_true", help="只检查源文件，不复制")
    args = parser.parse_args()

    missing = [str(src) for src, _ in COPIES if not src.is_file()]
    if missing:
        print("缺少源文件：", file=sys.stderr)
        for m in missing:
            print("  -", m, file=sys.stderr)
        return 1
    if args.check:
        print("检查通过：public 源文件齐全")
        return 0

    for src, dst in COPIES:
        copy_file(src, dst)
        print(f"[ok] {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

    n = copy_checkins()
    if n:
        print(f"[ok] checkin/W*.md -> public/checkin/（{n} 份 + index.html）")
    print("完成：public/ 已就绪，可以运行 vitepress build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
