---
layout: home

hero:
  name: AI 全栈 22 周作战包
  text: Java 后端 → AI 应用 / Agent 开发
  tagline: 2026-11-09 → 2027-04-11｜20h/周｜一个项目三次演进｜每日打卡 + 作战看板
  actions:
    - theme: brand
      text: 开始 22 周路线
      link: /docs/01-学习路线图
    - theme: alt
      text: 每日打卡系统
      link: /docs/03-每日打卡与精进系统
    - theme: alt
      text: 在线看板
      link: /docs/09-在线工具

features:
  - title: 目标反推，不是课程目录
    details: 从 2027 年 4 月 offer 倒推：W16 试水、W17 正式投、3 月主投，22 周每一步都有可验收产出。
  - title: 一个项目，三次演进
    details: Atlas：RAG 知识库 → Agent 工作台（MCP/状态图/HITL）→ 生产化（性能/成本/安全），面试能讲 30 分钟。
  - title: 每日最小闭环
    details: 输入 20min → 动手 60min → 复述 10min → 卡片 10min → commit 20min；另有 25 分钟最低限度版。
  - title: 离线看板 + 云端打卡
    details: 数据默认存浏览器；也可用 GitHub Actions 表单打卡，提交 data/checkins.json，Pages 看板自动读取。
---

## 这是什么

这是一套给**在职 Java 后端**准备的 22 周转型作战包，不是书单：

- **路线**：22 周、6 阶段、456h，目标 2027 年 4 月中前拿到 AI 应用 / Agent 开发 offer（20K 档）。
- **项目**：一个旗舰项目 Atlas，三次演进，带评测、权限、成本、安全、前端。
- **执行**：每周执行手册 + 每日 120 分钟闭环 + 周复盘 + 月回炉。
- **求职**：简历、题库、系统设计、手撕、模拟面试、投递、谈判。
- **工具**：离线打卡看板、周打卡生成器、GitHub Pages 部署、GitHub Actions 打卡。

## 先做 5 件事

1. 读 [00 · 目标与策略](/docs/00-目标与策略)，确认 20K 档的能力标准。
2. 打开 [01 · 学习路线图](/docs/01-学习路线图)，把 W1–W4 写进日历。
3. 打开 [09 · 打卡与看板](/docs/09-在线工具)，完成第一次打卡。
4. 按 [02 · 每周执行手册](/docs/02-每周执行手册) 做 W1 的 2 小时。
5. 发一条公开承诺，把链接贴进 W1 打卡。

## 22 周总览

| 阶段 | 周次 | 主题 | 关键产出 |
|---|---|---|---|
| P0 地基 | W1–W2 | 环境、模型、Prompt、工具调用 | 流式对话 + 模型横评 + 30 条评测集 |
| P1 应用核心 | W3–W5 | 上下文、安全、ReAct、立项 | 手写 agent loop + 100 条评测集 |
| P2 RAG | W6–W9 | 解析、检索、rerank、引用、评估 | Atlas v1 全栈 |
| P3 Agent | W10–W14 | MCP、状态图、HITL、记忆、多 Agent | Atlas v2 |
| P4 生产化 | W15–W17 | 性能、成本、安全、部署、投递 | Atlas v3 + 40 投递 |
| P5 求职 | W18–W22 | 题库、模拟、面试、谈判 | offer |

## 快速开始

```bash
# 本地开发（VitePress）
pnpm install
pnpm run docs:dev

# 生成 W1 打卡 + 打开看板
python3 scripts/gen_checkin.py --week 1
python3 -m http.server 8765
# 打开 http://127.0.0.1:8765/tracker/index.html

# 构建整站（GitHub Actions 也会跑）
pnpm run docs:build
```

> 部署到 GitHub Pages 后，把仓库 Settings → Pages → Source 设为 **GitHub Actions**。完整步骤见 [GitHub Pages 部署](/GITHUB_PAGES)。

## 数据与隐私

- 看板默认使用浏览器 `localStorage`，**不上传服务器**。
- 如果启用 GitHub Actions 打卡，记录会提交到仓库的 `data/checkins.json`；公开仓库意味着这些学习记录公开（不包含密钥）。
- 不要把 PAT、密码、公司内部文档放进仓库。
