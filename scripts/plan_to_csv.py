#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_to_csv.py —— 把 plan/plan.json 导出为 plan/plan.csv（UTF-8 BOM，Excel 双击可开）。

用法：
    python3 scripts/plan_to_csv.py                 # 生成 plan/plan.csv
    python3 scripts/plan_to_csv.py --out /tmp/x.csv
    python3 scripts/plan_to_csv.py --check         # 只校验并打印预览，不写文件

说明：
    * 输出带 BOM（utf-8-sig），避免 Excel 打开中文乱码；
    * 列表字段（目标 / 评估 / 产出）用「；」连接，保持单元格整洁；
    * 新增「阶段名称 / 阶段目标 / 里程碑」列，方便在 Excel 里筛选透视。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = ROOT / "plan" / "plan.json"
DEFAULT_OUT = ROOT / "plan" / "plan.csv"

HEADERS = [
    "周次", "开始日期", "结束日期", "阶段", "阶段名称", "周主题",
    "本周目标（Outcomes）", "项目任务", "评估指标（Eval）", "本周产出（Output）",
    "计划小时", "里程碑", "备注",
]


class CsvError(Exception):
    """可预期的用户错误。"""


def load_plan(path: Path) -> dict:
    if not path.is_file():
        raise CsvError(f"找不到计划文件：{path}（用 --plan 指定）")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CsvError(f"计划文件不是合法 JSON：{path}\n  {exc}") from exc
    if not isinstance(data.get("weeks"), list) or not data["weeks"]:
        raise CsvError(f"计划文件缺少 weeks 列表：{path}")
    return data


def join_list(value) -> str:
    if isinstance(value, list):
        return "；".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def build_rows(plan: dict) -> list[list[str]]:
    phases = {p.get("id"): p for p in plan.get("phases", [])}
    rows: list[list[str]] = []
    for week in plan["weeks"]:
        phase = phases.get(week.get("phase"), {})
        rows.append([
            str(int(week["week"])),
            str(week.get("start", "")),
            str(week.get("end", "")),
            str(week.get("phase", "")),
            str(phase.get("name", "")),
            str(week.get("theme", "")),
            join_list(week.get("outcomes")),
            str(week.get("project", "")),
            join_list(week.get("eval")),
            str(week.get("output", "")),
            str(week.get("hours", "")),
            "是" if week.get("milestone") else "否",
            str(week.get("note", "")),
        ])
    return rows


def write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADERS)
        writer.writerows(rows)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="plan_to_csv.py",
        description="把 plan/plan.json 导出为 Excel 友好的 CSV（UTF-8 BOM）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n  python3 scripts/plan_to_csv.py\n  python3 scripts/plan_to_csv.py --check",
    )
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN, metavar="FILE",
                        help=f"计划 JSON（默认 {DEFAULT_PLAN.relative_to(ROOT)}）")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, metavar="FILE",
                        help=f"输出 CSV（默认 {DEFAULT_OUT.relative_to(ROOT)}）")
    parser.add_argument("--check", action="store_true", help="只校验数据并打印预览，不写文件")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plan = load_plan(args.plan)
        rows = build_rows(plan)
        if args.check:
            print(f"校验通过：{len(rows)} 周，{len(HEADERS)} 列。")
            print(" | ".join(HEADERS))
            for row in rows[:3]:
                print(" | ".join(row[:6]))
            print("...")
            return 0
        write_csv(args.out, rows)
        size = args.out.stat().st_size
        rel = args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out
        print(f"[ok] 生成 {rel}：{len(rows)} 行 × {len(HEADERS)} 列，{size} 字节（UTF-8 BOM）")
        return 0
    except CsvError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"错误：读写文件失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
