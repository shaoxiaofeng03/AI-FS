#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_tracker.py —— 把 plan/plan.json 注入 tracker/template.html，生成单文件离线看板 tracker/index.html。

用法：
    python3 scripts/build_tracker.py            # 生成 tracker/index.html
    python3 scripts/build_tracker.py --check    # 只校验模板与数据，不写文件
    python3 scripts/build_tracker.py --out /tmp/index.html

说明：
    * 模板中用 __PLAN_DATA__ 占位，脚本替换为 plan.json 的 JSON（转义 </ 防止提前闭合 script）；
    * 生成物为单个 HTML，无外部依赖，file:// 或 python3 -m http.server 均可打开；
    * 不写入生成时间，同一 plan + 模板下重复构建结果一致。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = ROOT / "plan" / "plan.json"
DEFAULT_TEMPLATE = ROOT / "tracker" / "template.html"
DEFAULT_OUT = ROOT / "tracker" / "index.html"
MARKER = "__PLAN_DATA__"


class BuildError(Exception):
    """可预期的用户错误。"""


def load_plan(path: Path) -> dict:
    if not path.is_file():
        raise BuildError(f"找不到计划文件：{path}（用 --plan 指定）")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BuildError(f"计划文件不是合法 JSON：{path}\n  {exc}") from exc
    if not isinstance(data.get("meta"), dict) or not isinstance(data.get("weeks"), list) or not data["weeks"]:
        raise BuildError(f"计划文件缺少 meta / weeks 字段：{path}")
    return data


def load_template(path: Path) -> str:
    if not path.is_file():
        raise BuildError(f"找不到模板文件：{path}\n提示：模板应位于 tracker/template.html，或用 --template 指定。")
    text = path.read_text(encoding="utf-8")
    count = text.count(MARKER)
    if count == 0:
        raise BuildError(f"模板缺少数据占位符 {MARKER}：{path}")
    if count > 1:
        raise BuildError(f"模板中 {MARKER} 出现了 {count} 次（应只出现 1 次）：{path}")
    return text


def plan_payload(plan: dict) -> str:
    raw = json.dumps(plan, ensure_ascii=False, separators=(",", ":"))
    # 避免 JSON 中的 </script> 或 <!-- 提前结束 script 标签
    return raw.replace("</", "<\\/")


def build(plan: dict, template_text: str) -> str:
    payload = plan_payload(plan)
    html = template_text.replace(MARKER, payload)
    if MARKER in html:
        raise BuildError("数据注入失败：模板中仍残留占位符")
    if "</script>" in payload:  # 理论上已被转义，保留防御
        raise BuildError("计划数据包含无法安全注入的 </script> 片段")
    return html


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build_tracker.py",
        description="读取 plan/plan.json + tracker/template.html，生成离线单文件看板 tracker/index.html。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n  python3 scripts/build_tracker.py\n  python3 scripts/build_tracker.py --check",
    )
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN, metavar="FILE",
                        help=f"计划 JSON（默认 {DEFAULT_PLAN.relative_to(ROOT)}）")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, metavar="FILE",
                        help=f"HTML 模板（默认 {DEFAULT_TEMPLATE.relative_to(ROOT)}）")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, metavar="FILE",
                        help=f"输出 HTML（默认 {DEFAULT_OUT.relative_to(ROOT)}）")
    parser.add_argument("--check", action="store_true", help="只校验模板与数据，不写文件")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plan = load_plan(args.plan)
        template_text = load_template(args.template)
        html = build(plan, template_text)
        weeks = len(plan["weeks"])
        if args.check:
            print(f"校验通过：模板 1 个占位符，计划 {weeks} 周，预计产物 {len(html)} 字节。")
            return 0
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(html, encoding="utf-8", newline="\n")
        rel = args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out
        print(f"[ok] 生成 {rel}：{weeks} 周数据已注入，{len(html)} 字节")
        print("     打开方式：浏览器直接打开该文件，或 python3 -m http.server 后访问 /tracker/index.html")
        return 0
    except BuildError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"错误：读写文件失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
