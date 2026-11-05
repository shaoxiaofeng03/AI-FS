#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cloud_checkin.py —— 把打卡记录合并进 data/checkins.json。

支持两种输入：
  1) 命令行字段：--date / --hours / --focus / --link / --takeaway
  2) 看板导出的 JSON：--from-json <file>（读取 payload.data.records / checks）

用法：
  python3 scripts/cloud_checkin.py --date 2026-11-12 --hours 2 \
      --focus "Spring AI streaming" --takeaway "Flux 到 SSE 的封装"
  python3 scripts/cloud_checkin.py --from-json ~/Downloads/atlas-tracker-2026-11-12.json
  python3 scripts/cloud_checkin.py --from-json backup.json --date 2026-11-12 --hours 2.5
  python3 scripts/cloud_checkin.py --help

规则：
  * 日期格式 YYYY-MM-DD；默认今天（Asia/Shanghai）
  * 同一天重复写入时，新值覆盖旧值（补录/修正）
  * checks（每周交付物勾选）取并集，不丢进度
  * 写入是原子替换；--dry-run 只打印不落盘
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = ROOT / "data" / "checkins.json"
TZ = ZoneInfo("Asia/Shanghai")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class CloudCheckinError(Exception):
    pass


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def today_key() -> str:
    return datetime.now(TZ).date().isoformat()


def empty_data() -> dict:
    return {"version": 1, "updatedAt": now_iso(), "records": {}, "checks": {}}


def load_data(path: Path) -> dict:
    if not path.is_file():
        return empty_data()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CloudCheckinError(f"数据文件不是合法 JSON：{path}\n  {exc}") from exc
    if not isinstance(raw, dict):
        raise CloudCheckinError(f"数据文件格式错误（应为对象）：{path}")
    data = empty_data()
    data["version"] = int(raw.get("version", 1)) if str(raw.get("version", 1)).isdigit() else 1
    data["updatedAt"] = str(raw.get("updatedAt") or now_iso())
    if isinstance(raw.get("records"), dict):
        data["records"] = raw["records"]
    if isinstance(raw.get("checks"), dict):
        data["checks"] = raw["checks"]
    return data


def validate_date(text: str) -> str:
    if not DATE_RE.match(text):
        raise CloudCheckinError(f"日期格式应为 YYYY-MM-DD：{text}")
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise CloudCheckinError(f"日期不存在：{text}") from exc
    return text


def validate_hours(text: str) -> float:
    try:
        value = float(text)
    except (TypeError, ValueError) as exc:
        raise CloudCheckinError(f"小时数不是数字：{text}") from exc
    if not (0 < value <= 24):
        raise CloudCheckinError(f"小时数应在 0–24 之间：{value}")
    return round(value, 2)


def normalize_record(rec: dict) -> dict:
    if not isinstance(rec, dict):
        raise CloudCheckinError("records 中的记录必须是对象")
    hours = validate_hours(str(rec.get("hours", "")))
    return {
        "hours": hours,
        "focus": str(rec.get("focus", ""))[:2000],
        "link": str(rec.get("link", ""))[:1000],
        "takeaway": str(rec.get("takeaway", ""))[:1000],
        "updatedAt": str(rec.get("updatedAt") or now_iso()),
    }


def merge_checks(target: dict, incoming: dict) -> int:
    """把 incoming.checks 合并进 target.checks；按周取并集。返回合并周数。"""
    if not isinstance(incoming, dict):
        return 0
    n = 0
    for week, src in incoming.items():
        key = str(week)
        if not re.match(r"^\d{1,2}$", key) or not isinstance(src, dict):
            continue
        dst = target.setdefault(key, {"outcomes": [], "eval": [], "output": False})
        for field in ("outcomes", "eval"):
            a = dst.get(field) if isinstance(dst.get(field), list) else []
            b = src.get(field) if isinstance(src.get(field), list) else []
            size = max(len(a), len(b))
            dst[field] = [
                (bool(a[i]) if i < len(a) else False) or (bool(b[i]) if i < len(b) else False)
                for i in range(size)
            ]
        dst["output"] = bool(dst.get("output")) or bool(src.get("output"))
        n += 1
    return n


def merge_export(data: dict, payload: dict) -> tuple[int, int]:
    """合并看板导出的 JSON（payload.data 或裸 state）。"""
    src = payload.get("data") if isinstance(payload, dict) and isinstance(payload.get("data"), dict) else payload
    if not isinstance(src, dict):
        raise CloudCheckinError("导出的 JSON 中没有 data 对象")
    records = src.get("records")
    if not isinstance(records, dict):
        raise CloudCheckinError("导出的 JSON 缺少 records 字段")
    count = 0
    for date, rec in records.items():
        date = validate_date(str(date))
        data["records"][date] = normalize_record(rec)
        count += 1
    weeks = merge_checks(data["checks"], src.get("checks") or {})
    return count, weeks


def write_data(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updatedAt"] = now_iso()
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    # 原子替换，避免写一半
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(payload)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="cloud_checkin.py",
        description="合并打卡记录到 data/checkins.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python3 scripts/cloud_checkin.py --hours 2 --focus 'RAG 切分实验'\n"
            "  python3 scripts/cloud_checkin.py --from-json ~/Downloads/atlas-tracker-2026-11-12.json\n"
            "  python3 scripts/cloud_checkin.py --date 2026-11-12 --hours 2.5 --dry-run"
        ),
    )
    p.add_argument("--date", help="日期 YYYY-MM-DD，默认今天（Asia/Shanghai）")
    p.add_argument("--hours", help="投入小时数，如 2 或 2.5")
    p.add_argument("--focus", default="", help="今天做了什么")
    p.add_argument("--link", default="", help="产出链接（commit/博客/文档）")
    p.add_argument("--takeaway", default="", help="一句收获")
    p.add_argument("--from-json", type=Path, metavar="FILE", help="看板导出的 JSON 备份")
    p.add_argument("--file", type=Path, default=DEFAULT_FILE, metavar="FILE",
                   help=f"数据文件（默认 {DEFAULT_FILE.relative_to(ROOT)}）")
    p.add_argument("--dry-run", action="store_true", help="只打印结果，不写文件")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        data = load_data(args.file)
        exported = 0
        merged_weeks = 0

        if args.from_json:
            try:
                payload = json.loads(args.from_json.read_text(encoding="utf-8"))
            except FileNotFoundError:
                raise CloudCheckinError(f"找不到文件：{args.from_json}")
            except json.JSONDecodeError as exc:
                raise CloudCheckinError(f"不是合法 JSON：{args.from_json}\n  {exc}") from exc
            exported, merged_weeks = merge_export(data, payload)

        if args.date or args.hours or args.focus or args.link or args.takeaway:
            date = validate_date(args.date or today_key())
            if not args.hours:
                raise CloudCheckinError("写入单条记录时必须提供 --hours")
            hours = validate_hours(args.hours)
            data["records"][date] = {
                "hours": hours,
                "focus": str(args.focus or "")[:2000],
                "link": str(args.link or "")[:1000],
                "takeaway": str(args.takeaway or "")[:1000],
                "updatedAt": now_iso(),
            }
            print(f"[ok] 写入 {date}：{hours}h")
        elif not args.from_json:
            raise CloudCheckinError("没有输入：用 --hours/--focus 写一条，或 --from-json 合并备份")

        if args.dry_run:
            print(json.dumps(data, ensure_ascii=False, indent=2))
            print("[dry-run] 未写入")
            return 0

        write_data(args.file, data)
        total = len(data["records"])
        print(f"[ok] 已写入 {args.file}（records={total}，checks={len(data['checks'])} 周）")
        if args.from_json:
            print(f"[ok] 从备份合并：{exported} 条记录，{merged_weeks} 周勾选")
        return 0
    except CloudCheckinError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"错误：文件读写失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
