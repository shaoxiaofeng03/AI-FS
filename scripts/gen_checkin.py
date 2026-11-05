#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_checkin.py —— 根据 plan/plan.json 生成每周「每日打卡」Markdown 文件。

用法（在本仓库任意目录执行均可）：
    python3 scripts/gen_checkin.py --week 1        # 生成 checkin/W01-每日打卡.md
    python3 scripts/gen_checkin.py --all           # 生成全部 22 周（已存在的默认跳过）
    python3 scripts/gen_checkin.py --all --force   # 全部重新生成并覆盖
    python3 scripts/gen_checkin.py --week 3 --dry-run   # 只预览，不写文件

规则：
    * 文件名固定为 checkin/W{两位周号}-每日打卡.md；
    * 默认不覆盖已有文件（幂等），加 --force 才覆盖；
    * 日期按 plan.json 中各周 start 依次 +0~+6 天，保留周一~周日；
    * 不写入生成时间，同一 plan 下重复生成结果完全一致。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PLAN = ROOT / "plan" / "plan.json"
DEFAULT_TEMPLATE = ROOT / "checkin" / "templates" / "week.md"
DEFAULT_OUT_DIR = ROOT / "checkin"
FILE_PATTERN = "W{week:02d}-每日打卡.md"
WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
BASE_DAY_HOURS = [2, 2, 2, 2, 2, 6, 4]  # 标准 20h 周的节奏
TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


class GenCheckinError(Exception):
    """可预期的用户错误：打印清晰提示，退出码 1。"""


def load_plan(path: Path) -> dict:
    if not path.is_file():
        raise GenCheckinError(f"找不到计划文件：{path}\n提示：请在仓库根目录执行，或用 --plan 指定 plan.json 路径。")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GenCheckinError(f"计划文件不是合法 JSON：{path}\n  {exc}") from exc
    if not isinstance(data.get("meta"), dict) or not isinstance(data.get("weeks"), list) or not data["weeks"]:
        raise GenCheckinError(f"计划文件缺少 meta / weeks 字段：{path}")
    return data


def load_template(path: Path) -> str:
    if not path.is_file():
        raise GenCheckinError(f"找不到模板文件：{path}\n提示：模板应位于 checkin/templates/week.md，或用 --template 指定。")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise GenCheckinError(f"模板文件为空：{path}")
    return text


def planned_day_hours(total_hours: float) -> list[float]:
    """按标准 20h 节奏缩放，返回 7 天的建议投入（周日兜底使总和等于计划值）。"""
    try:
        total = float(total_hours)
    except (TypeError, ValueError):
        total = 20.0
    if total <= 0:
        total = 20.0
    scale = total / sum(BASE_DAY_HOURS)
    hours = [max(0.5, round(h * scale * 2) / 2) for h in BASE_DAY_HOURS[:6]]
    sunday = total - sum(hours)
    if sunday < 0.5:
        sunday = 0.5
    hours.append(round(sunday * 2) / 2)
    return hours


def fmt_hours(value: float) -> str:
    value = round(float(value), 1)
    return str(int(value)) if value == int(value) else f"{value:g}"


def day_focus(week: dict, index: int) -> str:
    """周一到周五依次对应该周 outcomes，周六项目深度块，周日验收+产出+复盘。"""
    project = str(week.get("project", "本周项目")).strip()
    outcomes = week.get("outcomes") or []
    if index <= 4:
        if index < len(outcomes):
            return str(outcomes[index]).strip()
        return f"推进项目：{project}"
    if index == 5:
        return f"项目深度块：{project}（3 × 90min，不切任务）"
    eval_items = week.get("eval") or []
    first_eval = str(eval_items[0]).strip() if eval_items else "本周验收指标"
    output = str(week.get("output", "本周产出")).strip()
    return f"验收 + 产出：对数字（{first_eval}），发布「{output}」"


def week_phase(plan: dict, week: dict) -> dict:
    phase_id = week.get("phase")
    for phase in plan.get("phases", []):
        if phase.get("id") == phase_id:
            return phase
    return {"id": phase_id or "-", "name": "未标注阶段", "goal": ""}


def next_week_hint(plan: dict, week: dict) -> str:
    weeks = plan["weeks"]
    current = int(week["week"])
    for candidate in weeks:
        if int(candidate["week"]) == current + 1:
            return f"W{int(candidate['week']):02d} · {candidate.get('theme', '')}"
    return "计划最后一周，收尾复盘、归档资产，准备入职"


def build_tokens(plan: dict, week: dict, template_text: str) -> dict:
    meta = plan["meta"]
    phase = week_phase(plan, week)
    start = dt.date.fromisoformat(str(week["start"]))
    dates = [start + dt.timedelta(days=i) for i in range(7)]
    hours = planned_day_hours(week.get("hours", 20))
    outcomes = [str(x).strip() for x in (week.get("outcomes") or [])]
    eval_items = [str(x).strip() for x in (week.get("eval") or [])]

    tokens = {
        "PLAN_TITLE": str(meta.get("title", "")).strip(),
        "TARGET": str(meta.get("targetOffer", "")).strip(),
        "WEEK": str(int(week["week"])),
        "WEEK2": f"{int(week['week']):02d}",
        "THEME": str(week.get("theme", "")).strip(),
        "PHASE_ID": str(phase.get("id", "")).strip(),
        "PHASE_NAME": str(phase.get("name", "")).strip(),
        "PHASE_GOAL": str(phase.get("goal", "")).strip(),
        "START": dates[0].isoformat(),
        "END": dates[6].isoformat(),
        "START_WD": WEEKDAY_CN[dates[0].weekday()],
        "END_WD": WEEKDAY_CN[dates[6].weekday()],
        "WEEK_HOURS": fmt_hours(week.get("hours", 20)),
        "MILESTONE": "⭐ 里程碑周" if week.get("milestone") else "普通周",
        "PROJECT": str(week.get("project", "")).strip(),
        "NOTE": str(week.get("note", "")).strip() or "按节奏推进，别攒到周末",
        "OUTCOMES": "\n".join(f"- [ ] {item}" for item in outcomes) or "- [ ] （本周未列目标）",
        "EVAL": "\n".join(f"- [ ] {item}" for item in eval_items) or "- [ ] （本周未列评估指标）",
        "OUTPUT": f"- [ ] **{week.get('output', '本周产出')}**",
        "NEXT_WEEK_HINT": next_week_hint(plan, week),
    }

    for i in range(7):
        key = f"D{i + 1}"
        focus = day_focus(week, i)
        # 表格单元格里不能出现竖线与换行
        tokens[f"{key}_DATE"] = dates[i].isoformat()
        tokens[f"{key}_MD"] = dates[i].strftime("%m/%d")
        tokens[f"{key}_WEEKDAY"] = WEEKDAY_CN[dates[i].weekday()]
        tokens[f"{key}_HOURS"] = fmt_hours(hours[i])
        tokens[f"{key}_FOCUS"] = re.sub(r"\s*\n\s*", " ", focus).replace("|", "/")
    return tokens


def render(template_text: str, tokens: dict, week_no: int) -> str:
    text = template_text
    for name, value in tokens.items():
        text = text.replace("{{" + name + "}}", value)
    leftovers = sorted(set(TOKEN_RE.findall(text)))
    if leftovers:
        raise GenCheckinError(
            f"模板中有未知占位符（W{week_no:02d}）：{', '.join(leftovers)}\n"
            "提示：占位符必须全部由 gen_checkin.py 提供，检查 checkin/templates/week.md 是否写错。"
        )
    if not text.endswith("\n"):
        text += "\n"
    return text


def target_path(out_dir: Path, week_no: int) -> Path:
    return out_dir / FILE_PATTERN.format(week=week_no)


def write_week(plan: dict, template_text: str, week: dict, out_dir: Path, force: bool, dry_run: bool) -> str:
    week_no = int(week["week"])
    content = render(template_text, build_tokens(plan, week, template_text), week_no)
    path = target_path(out_dir, week_no)
    existed = path.exists()
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    if dry_run:
        return f"[dry-run] W{week_no:02d} → {rel}（{len(content.splitlines())} 行，未写盘）"
    if existed and not force:
        return f"[skip] W{week_no:02d} 已存在：{rel}（需要覆盖请加 --force）"
    out_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    action = "覆盖" if existed else "生成"
    return f"[ok] {action} W{week_no:02d} → {rel}（{len(content.splitlines())} 行）"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gen_checkin.py",
        description="按 plan/plan.json 生成每周每日打卡 Markdown（默认不覆盖已有文件）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python3 scripts/gen_checkin.py --week 1\n"
            "  python3 scripts/gen_checkin.py --all\n"
            "  python3 scripts/gen_checkin.py --all --force\n"
            "  python3 scripts/gen_checkin.py --week 3 --dry-run"
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--week", type=int, metavar="N", help="只生成第 N 周（1~22）")
    group.add_argument("--all", action="store_true", help="生成计划中的全部周")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的文件（默认跳过）")
    parser.add_argument("--dry-run", action="store_true", help="只打印将生成的文件，不写盘")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, metavar="DIR",
                        help=f"输出目录（默认 {DEFAULT_OUT_DIR.relative_to(ROOT)}）")
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN, metavar="FILE",
                        help=f"计划 JSON（默认 {DEFAULT_PLAN.relative_to(ROOT)}）")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, metavar="FILE",
                        help=f"周模板（默认 {DEFAULT_TEMPLATE.relative_to(ROOT)}）")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        plan = load_plan(args.plan)
        template_text = load_template(args.template)
        weeks = {int(w["week"]): w for w in plan["weeks"]}
        if args.week is not None:
            if args.week not in weeks:
                valid = ", ".join(str(n) for n in sorted(weeks))
                raise GenCheckinError(f"周次 {args.week} 不在计划中。可选周次：{valid}")
            selected = [weeks[args.week]]
        else:
            selected = [weeks[n] for n in sorted(weeks)]

        results = []
        for week in selected:
            results.append(write_week(plan, template_text, week, args.out_dir, args.force, args.dry_run))
        print("\n".join(results))
        if not args.dry_run:
            created = sum(1 for r in results if r.startswith("[ok]"))
            skipped = len(results) - created
            print(f"\n完成：生成/覆盖 {created} 份，跳过 {skipped} 份（计划共 {len(weeks)} 周）。")
        return 0
    except GenCheckinError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"错误：读写文件失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
