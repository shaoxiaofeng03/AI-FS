# GitHub Pages 部署与打卡指南

> 目标：把文档、打卡看板、作战看板部署到 `https://<你的用户名>.github.io/<仓库名>/`，并且能用 GitHub Actions 在手机/电脑上打卡。
> 这个方案**不需要服务器、不需要数据库、不需要在浏览器里放 PAT**。
>
> **当前仓库**：`shaoxiaofeng03/AI-FS`｜**线上地址**：<https://shaoxiaofeng03.github.io/AI-FS/>｜**看板**：<https://shaoxiaofeng03.github.io/AI-FS/tracker/>

---

## 1. 方案总览

```
┌──────────────────────────────┐
│ GitHub 仓库（public）         │
│  ├─ docs/ + README + index   │
│  ├─ tracker/index.html       │
│  ├─ data/checkins.json       │  ← Actions 打卡写入
│  └─ .github/workflows/       │
│       ├─ deploy-pages.yml    │  ← 构建 VitePress → Pages
│       ├─ checkin.yml         │  ← 表单打卡 → commit 数据
│       └─ validate.yml        │  ← 校验 plan/脚本
└──────────────┬───────────────┘
               │ GitHub Actions
       ┌───────▼────────┐
       │ GitHub Pages   │
       │ 文档 + 看板     │
       └────────────────┘
```

- **文档**：VitePress 静态站，自动生成侧边栏/搜索/深色模式。
- **看板**：纯静态 HTML，部署在 `/tracker/`。
- **打卡**：Actions 表单 → 写 `data/checkins.json` → 触发 Pages 重新部署 → 看板自动读取云端数据。
- **本地优先**：没网/没登录也能用 localStorage 打卡，之后导出或提交。

---

## 2. 一次性部署（10 分钟）

### 2.1 创建仓库

当前仓库已创建：**`shaoxiaofeng03/AI-FS`**（public）。如果要新建，选 **public**（免费 Pages 要求 public；private 需要 GitHub Pro）。

### 2.2 推送代码

```bash
cd /home/sky/Documents/context/AI全栈
git init
git add .
git commit -m "feat: AI 全栈 22 周作战包 + Pages"
git branch -M main
git remote add origin git@github.com:shaoxiaofeng03/AI-FS.git
git push -u origin main
```

> 第一次 push 前确认 `.gitignore` 已排除 `node_modules/`、`.vitepress/cache/`、`.vitepress/dist/`。

### 2.3 开启 Pages

仓库 **Settings → Pages**：

- **Build and deployment → Source**：选 **GitHub Actions**。
- 不需要选分支；`deploy-pages.yml` 会构建并上传。

### 2.4 开启 Actions 写权限（打卡必需）

仓库 **Settings → Actions → General → Workflow permissions**：

- 选 **Read and write permissions**。
- 保存。

> 如果只部署不打卡，可以保持 read-only；但 `checkin.yml` 需要写 `data/checkins.json`。

### 2.5 触发部署

- 向 `main` push 一次，或
- 仓库 **Actions → Deploy GitHub Pages → Run workflow**。

完成后访问：

```
https://shaoxiaofeng03.github.io/AI-FS/
https://shaoxiaofeng03.github.io/AI-FS/tracker/
```

> 首次部署可能需要 1–2 分钟；如果 404，等 workflow 完成后再刷新。

---

## 3. base path 是怎么处理的

GitHub Pages 项目站点不是根域名，而是 `/<仓库名>/`。VitePress 必须设置 `base`，否则 CSS/JS 404。

- `deploy-pages.yml` 会自动判断：
  - 仓库名以 `.github.io` 结尾（用户/组织主页）→ `BASE_PATH=/`
  - 其他仓库 → `BASE_PATH=/<仓库名>/`
- 本地开发默认 `/`，不影响。
- **自定义域名**：在仓库 **Settings → Variables → Actions** 新建 `BASE_PATH`，值 `/`；然后重跑部署。
- 如果之后改了仓库名，重跑部署即可，不需要改代码。

---

## 4. 每日打卡（推荐方式）

### 4.1 在 GitHub 上打卡

1. 打开仓库 **Actions**。
2. 左侧选 **每日打卡（Cloud Check-in）**。
3. **Run workflow**，填写：
   - `date`：留空 = 今天（Asia/Shanghai）
   - `hours`：如 `2`
   - `focus`：今天做了什么
   - `link`：commit / 博客链接（可空）
   - `takeaway`：一句收获（可空）
4. 运行结束后，`data/checkins.json` 会新增/更新当天记录，并触发 Pages 重新部署。
5. 打开 `/tracker/`，看板会自动加载云端数据。

> 手机：GitHub App → 仓库 → Actions → 选择 workflow → Run workflow。
> 想看「连续打卡」和 22 周进度，直接打开看板即可。

### 4.2 手动提交（补录/批量）

```bash
# 方式 A：命令行补一条
python3 scripts/cloud_checkin.py --date 2026-11-12 --hours 2 \
  --focus "Atlas 解析 pipeline" --link "https://github.com/..." --takeaway "表格切分要整块"

# 方式 B：看板导出 JSON 后合并
python3 scripts/cloud_checkin.py --from-json ~/Downloads/atlas-tracker-2026-11-12.json

git add data/checkins.json
git commit -m "checkin: 2026-11-12"
git push
```

### 4.3 只用浏览器本地

不配置 Actions 也能用：看板保存到 localStorage，换设备用「导出/导入 JSON」。适合先跑起来。

---

## 5. 目录与文件

| 路径 | 说明 | 是否提交 |
|---|---|---|
| `.vitepress/config.mts` | VitePress 配置（base、侧边栏、搜索） | ✅ |
| `index.md` | Pages 首页 | ✅ |
| `docs/` | 00–09 文档 | ✅ |
| `README.md` / `DECISIONS.md` / `ERRORS.md` | 总览与复盘 | ✅ |
| `research/` | 市场调研 | ✅ |
| `tracker/index.html` | 看板构建产物 | ✅（也可重新生成） |
| `data/checkins.json` | 云端打卡数据 | ✅ |
| `public/` | 构建时生成（tracker/plan/data/checkin 副本） | ❌（`.gitignore`） |
| `node_modules/` / `.vitepress/cache/` / `.vitepress/dist/` | 依赖与构建产物 | ❌ |

---

## 6. 常见问题

### Q1：Pages 页面 404

- 确认 **Settings → Pages → Source = GitHub Actions**。
- 确认 `Deploy GitHub Pages` workflow 成功。
- 项目站点地址是 `https://<user>.github.io/<repo>/`，不是 `https://<user>.github.io/`。
- 刚部署完等 1–2 分钟。

### Q2：页面能开但 CSS/JS 404

- `base` 配错。项目站点应为 `/<repo>/`；自定义域名应为 `/`。
- 本仓库的 `deploy-pages.yml` 会自动算；自定义域名时设 `BASE_PATH=/` 变量。

### Q3：Actions 打卡报 `Permission denied` / 不能 push

- **Settings → Actions → General → Workflow permissions** 改成 **Read and write**。
- 确认 workflow 里有 `permissions: contents: write`。

### Q4：看板没有加载云端数据

- 打开浏览器控制台看 `../data/checkins.json` 是否 200。
- 确认 `data/checkins.json` 已提交，且 Pages 重新部署过。
- 看板在 `file://` 下无法 fetch，属正常；用 HTTP 服务或 Pages。

### Q5：localStorage 被禁用

- 无痕模式/部分浏览器会禁用；看板顶部有提示。用「导出 JSON」保存，或改用 Actions 打卡。

### Q6：仓库 private 能用 Pages 吗？

- 需要 GitHub Pro/Team；否则 Pages 只能 public。打卡数据也会公开，介意就用本地模式或外部后端。

### Q7：自定义域名怎么配？

1. 域名 DNS 加 CNAME 指向 `<user>.github.io`。
2. 仓库 Settings → Pages → Custom domain 填写域名。
3. Settings → Variables → Actions 新增 `BASE_PATH=/`。
4. 重跑部署。
5. 如需 CNAME 文件，可放到 `public/CNAME`（VitePress 会原样复制）。

### Q8：能不能自动提醒打卡？

可以加一个定时 workflow（cron）检查当天是否有记录，没有就创建 issue 提醒。当前未内置，避免过度打扰；需要的话可以在 `checkin.yml` 旁边加 `reminder.yml`（`schedule` + `issues: write`）。

---

## 7. 安全与隐私

- **不在浏览器里放 PAT**：当前方案用 GitHub Actions 的 `GITHUB_TOKEN`，不暴露个人令牌。
- 仓库是 public 时，`data/checkins.json` 公开；不要写公司内部信息、密钥、客户数据。
- 看板的「产出链接」也不要放内网地址。
- Actions 的 `GITHUB_TOKEN` 权限最小化：`contents: write`（打卡）/ `pages: write`（部署）。
- 如果以后接入 Supabase/Cloudflare Worker，把密钥放服务端环境变量，不要提交。

---

## 8. 本地预览与构建

```bash
pnpm install
pnpm run docs:dev          # 本地开发 http://localhost:5173
pnpm run docs:build        # 产物 .vitepress/dist
pnpm run docs:preview      # 预览构建产物

python3 scripts/prepare_site.py   # 只复制 tracker/plan/data 到 public
```

> 构建前 `prepare_site.py` 会把 `tracker/index.html`、`plan/plan.json`、`data/checkins.json`、`checkin/*.md` 复制到 `public/`，所以 VitePress 站点里可以直接访问 `/tracker/`、`/plan/plan.json`、`/checkin/`。

---

## 9. 这套方案能做什么、不能做什么

| 能力 | 支持 | 说明 |
|---|---|---|
| 文档站 + 搜索 + 深色模式 | ✅ | VitePress |
| 每日打卡 + 连续天数 + 22 周进度 | ✅ | 看板 + localStorage |
| 多设备同步 | ✅（提交式） | Actions 写 JSON，Pages 读取；延迟 20–60s |
| 多人协作 | ❌ | 纯静态，无实时后端 |
| 自动提醒 | ⚠️ 可扩展 | cron + issue |
| 私有数据 | ⚠️ | public 仓库会公开；private 需 Pro |
| 离线使用 | ✅ | 看板断网可用；文档构建后静态 |
| 移动端 | ✅ | 响应式；可加到桌面 |

> 结论：**个人学习打卡 + 文档站 + 作战看板，GitHub Pages 完全够用**；需要实时/多人/私密，再上 Supabase 或 Cloudflare Worker。
