# 学习工具使用说明

> 配套 `plan/plan.json`（22 周 · 6 阶段）的打卡与看板工具。所有工具**纯 Python3 标准库 + 原生 HTML/CSS/JS**，无外部依赖，断网可用。

## 1. 每周打卡文件生成器

```bash
python3 scripts/gen_checkin.py --week 1        # 生成 checkin/W01-每日打卡.md
python3 scripts/gen_checkin.py --all           # 生成全部 22 周（已存在默认跳过）
python3 scripts/gen_checkin.py --all --force   # 全部重新生成并覆盖
python3 scripts/gen_checkin.py --week 3 --dry-run   # 只看会生成什么
```

- 文件命名：`checkin/W{两位周号}-每日打卡.md`，自动填周一~周日的日期、周主题、本周目标、验收指标、产出、每日建议与周日复盘；
- 默认**不覆盖**已有文件（幂等），改完模板想批量重生成时再加 `--force`；
- 想改打卡格式：编辑 `checkin/templates/week.md`（占位符会由脚本填充，未知占位符会报错提醒）。

## 2. 离线看板

```bash
python3 scripts/build_tracker.py     # 生成 tracker/index.html（把 plan.json 注入模板）
```

打开 `tracker/index.html` 即可（双击 file:// 打开，或 `python3 -m http.server` 后访问 `/tracker/index.html`）。

- 今日视图 / 每日打卡（日期、小时、专注内容、产出链接、一句收获）/ 连续打卡 / 22 周进度网格 / 每周交付物勾选 / 统计 / 打印；
- 数据存在浏览器 `localStorage`，键名 `atlas-tracker-v1`；换浏览器或清缓存前用「导出 JSON 备份」；
- 导入会校验格式并二次确认，重置不可撤销；
- 部署到 GitHub Pages 后，看板会自动读取 `../data/checkins.json` 并合并（云端打卡由 GitHub Actions 写入）；
- 数据默认不上传；只有你主动用 Actions/手动提交时，记录才会进仓库。

## 3. 计划导出 CSV（Excel）

```bash
python3 scripts/plan_to_csv.py                 # 生成 plan/plan.csv（UTF-8 BOM）
python3 scripts/plan_to_csv.py --check         # 只看校验结果
```

## 4. GitHub Pages + 云端打卡

```bash
# 本地构建整站
pnpm install
pnpm run docs:build

# 云端补录一条（写入 data/checkins.json）
python3 scripts/cloud_checkin.py --hours 2 --focus "RAG 切分实验" --takeaway "结构感知切分"

# 从看板导出的 JSON 合并
python3 scripts/cloud_checkin.py --from-json ~/Downloads/atlas-tracker-2026-11-12.json

# 校验数据
python3 scripts/validate_plan.py
```

- 完整部署步骤见根目录 `GITHUB_PAGES.md`；
- GitHub Actions 打卡：仓库 **Actions → 每日打卡（Cloud Check-in）→ Run workflow**；
- 看板「云端备份 / 手机打卡」卡片可手动「从云端加载 / 合并」，并自动识别 `*.github.io/<repo>` 仓库链接；
- 记录会公开在 `data/checkins.json`（public 仓库），不要写公司机密/密钥。

## 5. 数据源与目录

```
plan/plan.json          # 唯一权威数据源（22 周计划，勿改结构）
plan/plan.csv           # 脚本导出的 Excel 版（可重新生成）
checkin/templates/week.md   # 周打卡模板
checkin/W01..W22-每日打卡.md # 生成好的每周打卡文件
tracker/template.html   # 看板模板（含 __PLAN_DATA__ 占位符）
tracker/index.html      # 构建产物（勿手改）
scripts/                # 生成器/构建器/导出器/云合并/校验
data/checkins.json      # 云端打卡数据（Actions 写入，可手动合并）
.github/workflows/      # Pages 部署 / Actions 打卡 / 校验
.vitepress/config.mts   # VitePress 站点配置
```

改计划：只改 `plan/plan.json` 的周内容，然后重新执行 `gen_checkin.py --all --force` 与 `build_tracker.py`；`plan.csv` 用 `plan_to_csv.py` 重新导出；站点用 `pnpm run docs:build` 重建。
