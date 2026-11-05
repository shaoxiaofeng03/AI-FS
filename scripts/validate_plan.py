#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_plan.py —— 校验计划/打卡/云端数据的结构与一致性。

用于 CI（.github/workflows/validate.yml）和本地提交前检查：
  python3 scripts/validate_plan.py
  python3 scripts/validate_plan.py --strict   # 额外检查 checkin 文件与日期
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "plan" / "plan.json"
DATA = ROOT / "data" / "checkins.json"
TRACKER = ROOT / "tracker" / "index.html"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Fail(Exception):
    pass


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise Fail(msg)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Fail(f"找不到文件：{path}")
    except json.JSONDecodeError as exc:
        raise Fail(f"JSON 格式错误：{path}\n  {exc}") from exc


def validate_plan() -> int:
    plan = load_json(PLAN)
    check(isinstance(plan.get("meta"), dict), "plan.json 缺少 meta")
    weeks = plan.get("weeks")
    check(isinstance(weeks, list) and len(weeks) == 22, f"周数应为 22，实际 {len(weeks) if isinstance(weeks, list) else 'N/A'}")
    phase_ids = {p.get("id") for p in plan.get("phases", [])}
    total_hours = 0.0
    seen = set()
    for i, w in enumerate(weeks, start=1):
        check(w.get("week") == i, f"第 {i} 个周的 week 字段不是 {i}")
        check(w.get("week") not in seen, f"周次重复：{w.get('week')}")
        seen.add(w.get("week"))
        check(w.get("phase") in phase_ids, f"W{i} 的 phase 未在 phases 中定义：{w.get('phase')}")
        start = dt.date.fromisoformat(w["start"])
        end = dt.date.fromisoformat(w["end"])
        check(start.weekday() == 0, f"W{i} 开始日期不是周一：{start}")
        check((end - start).days == 6, f"W{i} 结束日期不是开始 + 6 天")
        check(float(w.get("hours", 0)) > 0, f"W{i} hours 必须 > 0")
        total_hours += float(w.get("hours", 0))
        check(len(w.get("outcomes") or []) >= 3, f"W{i} outcomes 少于 3 条")
        check(len(w.get("eval") or []) >= 1, f"W{i} eval 少于 1 条")
        check(bool(w.get("output")), f"W{i} 缺少 output")
    check(abs(total_hours - 456) < 0.01, f"总小时数应为 456，实际 {total_hours}")
    check(plan["meta"].get("start") == weeks[0]["start"], "meta.start 与 W1.start 不一致")
    check(plan["meta"].get("end") == weeks[-1]["end"], "meta.end 与 W22.end 不一致")
    print(f"[ok] plan.json：22 周，{total_hours:g}h，{len(plan.get('phases', []))} 个阶段")
    return 0


def validate_checkin_files(strict: bool) -> int:
    plan = load_json(PLAN)
    missing = []
    for w in plan["weeks"]:
        p = ROOT / "checkin" / f"W{w['week']:02d}-每日打卡.md"
        if not p.is_file():
            missing.append(str(p.relative_to(ROOT)))
            continue
        if strict:
            text = p.read_text(encoding="utf-8")
            check(w["start"] in text and w["end"] in text, f"{p.name} 日期与 plan 不一致")
    if missing:
        raise Fail("缺少打卡文件：\n  " + "\n  ".join(missing))
    print(f"[ok] checkin：22 份周文件{'' if strict else '（未逐份校验日期）'}")
    return 0


def validate_cloud_data() -> int:
    if not DATA.is_file():
        print("[skip] data/checkins.json 不存在（可先运行一次 Actions 打卡或 cloud_checkin.py）")
        return 0
    data = load_json(DATA)
    check(isinstance(data, dict), "checkins.json 应为对象")
    records = data.get("records")
    check(isinstance(records, dict), "checkins.json 缺少 records 对象")
    for date, rec in records.items():
        check(bool(DATE_RE.match(str(date))), f"非法日期：{date}")
        try:
            dt.date.fromisoformat(str(date))
        except ValueError as exc:
            raise Fail(f"日期不存在：{date}") from exc
        check(isinstance(rec, dict), f"{date} 的记录应为对象")
        hours = float(rec.get("hours", 0))
        check(0 < hours <= 24, f"{date} 的 hours 超出 0–24：{hours}")
    checks = data.get("checks", {})
    check(isinstance(checks, dict), "checkins.json 的 checks 应为对象")
    print(f"[ok] checkins.json：{len(records)} 条记录，{len(checks)} 周勾选")
    return 0


def validate_tracker() -> int:
    check(TRACKER.is_file(), "缺少 tracker/index.html（运行 python3 scripts/build_tracker.py）")
    text = TRACKER.read_text(encoding="utf-8")
    check("plan-data" in text, "tracker/index.html 缺少注入的 plan-data")
    check("atlas-tracker-v1" in text, "tracker/index.html 缺少 localStorage 键")
    print("[ok] tracker/index.html 存在且包含 plan-data")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="校验计划与打卡数据")
    parser.add_argument("--strict", action="store_true", help="逐份校验 checkin 文件日期")
    parser.add_argument("--data-only", action="store_true", help="只校验 data/checkins.json")
    args = parser.parse_args()
    try:
        if args.data_only:
            validate_cloud_data()
        else:
            validate_plan()
            validate_checkin_files(args.strict)
            validate_tracker()
            validate_cloud_data()
        print("全部校验通过。")
        return 0
    except Fail as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
