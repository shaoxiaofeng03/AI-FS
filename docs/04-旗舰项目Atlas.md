# 04 · 旗舰项目 Atlas：企业知识库 + Agent 工作台

> **一个项目，三次演进**：v1 RAG 知识库（W6–W9）→ v2 Agent Harness（W10–W14）→ v3 生产化（W15–W17）。
> 目的不是「做一个聊天机器人」，而是造一个**能在面试里讲 30 分钟、每个模块都有数字和取舍**的作品。
> 项目名 Atlas 只是代号，你可以换成任何名字；重要的是结构和证据。

---

## 1. 为什么是一个项目做三次，而不是三个项目

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| 三个独立项目 | 覆盖面广 | 每个都浅；22 周做不完；面试讲不深 | ❌ |
| 一个项目三次演进 | 有深度、有故事线、能讲取舍、省时间 | 需要提前设计演进路径 | ✅ |
| 只做 RAG 不做 Agent | 稳 | 错过 Agent 岗的最大缺口 | ❌ |
| 只做 Agent 不做 RAG | 酷 | 没有检索与评测地基，Agent 也不稳 | ❌ |

**演进故事线**（面试就按这个讲）：

> 我先做了 RAG 知识库，解决了「企业文档找不到、答不准」；上线后发现用户要的不是问答，而是「帮我把事做完」，于是加了工具与状态图；工具一多就出现权限、失败恢复、审批和成本问题，于是做了 Agent Harness 和生产化治理。

这条线天然包含：需求 → 架构 → 评测 → 故障 → 优化 → 治理，面试官会顺着问。

---

## 2. 项目定位

| 项 | 内容 |
|---|---|
| 一句话 | 面向企业内部技术支持/售前/运维的 AI 工作台：能查文档、能调工具、能走审批、能算成本 |
| 目标用户 | 一线支持工程师、售前、运维、内部员工 |
| 核心场景 | ① 文档问答与引用 ② 多步任务（查工单→查库存→生成方案） ③ 高风险操作人工审批 ④ 知识运营与评估 |
| 不做什么 | 不做通用聊天、不做模型训练、不做 C 端产品、不做复杂的低代码编排器 |
| 成功指标 | 回答准确、引用可点、任务能完成、权限不越界、成本可控 |
| 演示形态 | Web 应用 + 3 分钟视频 + 在线 demo（可选） |

**边界很重要**：面试官问「你为什么不做 XX」时，你要能说出「因为目标用户不需要/时间不够/有更简单的替代方案」。

---

## 3. 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js 前端（React 19）                  │
│  聊天 / 引用面板 / 工具时间线 / 审批弹窗 / 管理后台 / 评估看板      │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST + SSE
┌───────────────────────────────▼─────────────────────────────────┐
│                     Spring Boot 后端（Java 21+）                 │
│  Auth / Tenant / Quota / Audit                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  RAG 模块     │  │ Agent 运行时  │  │ 模型网关 ModelGateway │   │
│  │ 检索/重排/引用 │  │ 状态图/工具/  │  │ 路由/降级/缓存/计费   │   │
│  │ 权限过滤      │  │ 记忆/HITL     │  │                      │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
   ┌──────▼─────┐    ┌──────▼──────┐       ┌──────▼──────┐
   │ PostgreSQL  │    │ MCP 工具服务 │       │ LLM Providers│
   │ + pgvector  │    │ Java/Python │       │ DeepSeek/Qwen │
   │ + 全文索引   │    │ 内部 API     │       │ Claude/GPT   │
   └────────────┘    └─────────────┘       └─────────────┘
          │
   ┌──────▼─────┐    ┌──────────────┐    ┌──────────────┐
   │ Redis       │    │ MinIO/S3     │    │ Langfuse/OTel │
   │ 缓存/会话/队列│   │ 原始文档      │    │ Trace/成本    │
   └────────────┘    └──────────────┘    └──────────────┘
          │
   ┌──────▼──────────────────────────────────────────────┐
   │ Python 侧车：解析（docling/unstructured）、评估（RAGAS/DeepEval）、 │
   │ 数据脚本；通过 CLI / 队列 / HTTP 与主服务解耦            │
   └──────────────────────────────────────────────────────┘
```

### 3.1 技术栈与理由

| 层 | 选择 | 理由 | 备选/改选条件 |
|---|---|---|---|
| 后端 | Java 21 + Spring Boot 3.5+/4.x | 存量优势、企业生态、虚拟线程 | 团队全 Python 时改 FastAPI |
| AI 框架 | **Spring AI 2.0.x** | 2026-06 GA；ChatClient/Advisor/结构化输出/向量抽象；2.1 的 Session Memory / 工具确认可加分 | LangChain4j 1.23（API 更简洁） |
| 编排 | **LangGraph4j 1.8.8**（主）或 ADK for Java 1.0 | 状态图/checkpoint/HITL；JVM 可落地 | Python LangGraph（生态更全）；SAA 1.1.2 仅作对照 |
| 检索 | PostgreSQL + pgvector 0.8.x + 全文索引 | 与业务表 JOIN 做权限；部署简单 | ES kNN / Milvus / Qdrant |
| 缓存 | Redis | 会话、限流、语义缓存 | Caffeine（单机） |
| 对象存储 | MinIO | 本地可跑，S3 兼容 | 阿里云 OSS |
| 前端 | Next.js 16 + React 19 + TS + Tailwind + shadcn/ui + AI SDK 6 | 一条主线；流式/工具 UI 生态好 | Vite + React（更轻） |
| 可观测 | OpenTelemetry + Langfuse | trace/成本/评测一体 | LangSmith / Phoenix |
| 评估 | Python + RAGAS/DeepEval + 自建 judge；Java 侧可用 langchain4j-test Judge | 生态成熟；CI 可跑 | promptfoo |
| AI 编程 | Claude Code / Codex + CLAUDE.md | 2026 JD 已把「重度使用」写进要求；也是效率杠杆 | Cursor / Aider |
| 部署 | Docker Compose；K8s 基础 | 22 周够用；能讲清即可 | 云托管 |

> **Spring AI Alibaba 的坑（2026-11 调研）**：截至 2026-11 可查最新为 1.1.2.0（对齐 Spring AI 1.1.2），未核实到对齐 Spring AI 2.x 的版本；社区有「重心转向 AgentScope」的讨论。**作品集二选一，不要和 Spring AI 2.x 混用**；目标 JD 明确点名 SAA 时再投入，平时只作对照。

### 3.2 关键设计决策（写进 DECISIONS.md）

1. 为什么用 pgvector 而不是 Milvus？
2. 为什么混合检索？权重怎么定？
3. 为什么需要 rerank？收益/延迟比？
4. 为什么状态图而不是 chain？
5. 为什么 MCP？和普通 tool calling 的区别？
6. checkpoint 存什么？怎么保证幂等？
7. 多租户怎么做隔离？
8. 成本怎么算？降本做了什么？
9. 为什么前端用 Next.js？SSR 用在哪？
10. 为什么解析用 Python 侧车？

每一条都要有：备选、判据、实测数字、代价、改选条件。

---

## 4. 数据模型（最小可用）

```sql
-- 租户与权限
tenant(id, name, plan, quota_monthly_tokens, created_at)
app_user(id, tenant_id, email, password_hash, role, created_at)
document(id, tenant_id, title, source_type, source_uri, owner_id, acl_json, status, version, created_at, updated_at)
document_version(id, document_id, version, checksum, storage_key, parsed_at)
chunk(id, tenant_id, document_id, version, chunk_no, content, token_count, metadata_json, embedding vector(1024), tsv tsvector)
conversation(id, tenant_id, user_id, title, created_at, updated_at)
message(id, conversation_id, role, content, citations_json, token_in, token_out, latency_ms, created_at)
run(id, tenant_id, conversation_id, agent_name, status, input_json, output_json, cost_cents, latency_ms, trace_id, created_at)
run_step(id, run_id, step_no, type, name, input_json, output_json, status, error, started_at, ended_at)
tool(id, tenant_id, name, version, schema_json, risk_level, enabled)
tool_call(id, run_id, tool_id, args_json, result_json, status, idempotency_key, approved_by, created_at)
approval(id, run_id, tool_call_id, status, requested_at, decided_at, decided_by, comment)
memory(id, tenant_id, user_id, type, content, embedding vector(1024), confidence, expires_at, created_at)
eval_case(id, tenant_id, category, question, reference_answer, reference_docs_json, difficulty)
eval_run(id, dataset_version, model_config, metrics_json, created_at)
eval_result(id, eval_run_id, case_id, answer, retrieved_json, scores_json, latency_ms, cost_cents)
feedback(id, tenant_id, message_id, user_id, rating, comment, created_at)
audit_log(id, tenant_id, actor_id, action, resource, detail_json, ip, created_at)
model_usage(id, tenant_id, run_id, provider, model, prompt_tokens, completion_tokens, cost_cents, latency_ms, created_at)
```

**要点**

- 所有业务表带 `tenant_id`；检索 SQL 必须带租户与 ACL 过滤，**在数据库层做，不只在应用层做**。
- `chunk.embedding` 的维度要与 embedding 模型一致；换模型要重建索引（写进 ADR）。
- `document_version` 支持增量与回滚。
- `tool_call.idempotency_key` 保证重试不重复执行。
- `audit_log` 记录高风险操作（审批、删除、导出）。

---

## 5. 模块拆解与实现要点

### 5.1 文档接入与解析（W6）

**流程**：上传 → 校验 → 存储（MinIO）→ 解析 → 清洗 → 切分 → 元数据/ACL → 向量化 → 入库 → 索引状态。

**要点**

- 支持 PDF/Word/HTML/Markdown；表格优先转 Markdown。
- 解析失败可重试、可人工修正；记录失败原因。
- 扫描件 OCR 作为可选（Tesseract/PaddleOCR），成本高，只对关键文档。
- 清洗：页眉页脚、页码、乱码、重复段落、水印。
- 元数据：标题、章节、来源、更新时间、ACL、租户。
- 增量：checksum 不变则跳过；变更则新版本 + 重建该文档 chunk。

**度量**：解析成功率、平均耗时、失败类型 top 5、chunk 数/文档、平均 token/chunk。

### 5.2 切分（W6）

| 策略 | 适用 | 优点 | 缺点 |
|---|---|---|---|
| 固定窗口 | 结构差的文本 | 简单 | 切断语义 |
| 递归分隔符 | 通用 | 保留段落/标题 | 依赖格式 |
| 语义切分 | 长文/论文 | 语义完整 | 慢、成本高 |
| 父子块 | 问答/多粒度 | 子块检索、父块生成 | 索引体积大 |
| 结构感知 | 手册/制度 | 保留章节 | 解析要求高 |

**实验**：chunk size ∈ {256, 512, 1024} × overlap ∈ {0, 50, 100}，固定 embedding/检索，测 recall@5 + 平均上下文 token。

### 5.3 检索（W7）

- 向量：pgvector HNSW（`m`, `ef_construction`），查询 `ef_search`；余弦距离。
- 关键词：Postgres `tsvector`（中文用 zhparser/pg_jieba）或 ES + IK。
- 融合：RRF（`score = Σ 1/(k + rank)`），或加权归一化；记录权重。
- 过滤：tenant_id、ACL、文档状态、时间、标签；**先过滤再检索**，避免越权与噪声。
- 查询改写（可选）：多查询、同义词、HyDE；每条都要评测收益。
- 度量：recall@5/10、MRR、nDCG@10、P95 延迟、索引构建时间。

### 5.4 Rerank 与生成（W8）

- Rerank：bge-reranker-v2-m3（API/本地）或 Cohere；top 50 → top 8。
- 上下文组装：按相关性 + 多样性 + token 预算；去重；保留来源与段落号。
- 引用：每个论断绑定 chunk id；前端可点击跳转高亮。
- 拒答：无证据、低分、冲突、超出范围时明确说「不知道」。
- 输出：结论 → 依据 → 引用；支持流式。
- 度量：faithfulness、answer relevance、correctness、citation precision/recall、拒答准确率。

### 5.5 工具平台与 MCP（W10）

- 工具注册：name/version/schema/risk_level/timeout/retry/owner。
- 执行：参数校验、超时、重试、幂等、沙箱、审计。
- 风险分级：只读（自动）/写操作（审批）/高危（双人审批/禁用）。
- **MCP 按 2026-07-28 规范**：无状态（去 session/initialize）、`server/discover`、`subscriptions/listen`、MRTR（`input_required` 承载人工确认）、tasks 扩展；传输用 stdio / Streamable HTTP。**2025 年教程的 session/SSE 写法已过时**。
- 落地前先实测：Spring AI / LangChain4j 的 MCP 客户端/服务端是否已跟进 2026-07-28；没跟进就锁定旧版规范并在文档里写清楚，不要混着讲。
- 工具示例：`search_ticket`、`get_order`、`create_ticket`、`query_inventory`、`send_email_mock`。
- 度量：工具调用成功率、错误率、P95、审批率、越权尝试数。

### 5.6 状态图与 HITL（W11）

```
START → 理解意图 → 规划 → [检索?] → [工具?] → 审批? → 执行 → 观察 → 继续/结束
                         ↑                              │
                         └──────── 条件分支/循环 ────────┘
```

- 状态：messages、plan、tool_results、retrieved_docs、budget、approval、error。
- 实现：优先 **LangGraph4j**（Java 版 LangGraph 思路）；SAA Graph / ADK Java 只做同功能对照；Spring AI 2.x 的 `@Tool(requiresConfirmation = true)` 可直接支撑「工具确认」。
- checkpoint：每步持久化；恢复时从最后成功步继续；幂等键防重复副作用。
- HITL：暂停 → 通知 → 审批/拒绝/修改 → 恢复；超时自动拒绝；审批人权限校验；MCP MRTR 可作为协议层实现。
- 终止条件：任务完成、最大步数、预算耗尽、连续错误、用户取消。
- 度量：任务成功率、平均步数、恢复成功率、审批等待时长、人工干预率。

### 5.7 记忆（W12）

> **先看框架**：Spring AI 2.1 的 Session Memory 已经提供「append-only 事件日志 + 按回合压缩」（`TurnCountTrigger` + `WindowCompactionStrategy`），并支持 JDBC 存储。先评估能否直接复用，再决定自研哪些部分；不要为了「自研」而自研。

| 类型 | 存什么 | 存储 | 读取 |
|---|---|---|---|
| 短期 | 最近 N 轮、当前任务状态 | Redis/内存 | 直接拼上下文 |
| 摘要 | 会话摘要、决策 | Postgres | 每 N 轮更新 |
| 长期事实 | 用户偏好、业务实体 | Postgres | 按用户/租户查 |
| 语义记忆 | 历史问题/答案 | pgvector | 相似检索 |
| 画像 | 角色、常用系统、权限 | Postgres | 注入 system |

**要点**：写入要审核（防污染）；读取要限 token；过期/删除要支持；冲突以最新+置信度处理；**工具调用与结果不能被回合压缩切断**。

### 5.8 多 Agent（W14）

- supervisor：分解任务、分派、汇总、终止。
- 专家：检索 Agent、分析 Agent、写作 Agent、工具 Agent。
- handoff：上下文裁剪后传递，避免全量历史。
- 代价：token × 轮数、延迟、调试复杂度；**先证明单 Agent 不够用**。
- 度量：成功率、成本、延迟、冲突率；与单 Agent 对比。

### 5.9 模型网关（W15）

- 统一接口：chat/stream/embed/rerank。
- 路由：按任务/成本/延迟/可用性选模型。
- 降级：主模型失败 → 备用 → 小模型 → 缓存/兜底话术。
- 灰度：按租户/比例切换 prompt/模型；可回滚。
- 计费：token 账本、按租户/会话/功能统计。
- 缓存：精确 + 语义（阈值 + 白名单 + 失效）。
- 参考 LangChain4j 1.23 的 **Decision Model / Confidence Cascade**：便宜档先答，置信度不足再升档；可作为「成本-质量」路由的一种实现。
- 度量：成本/会话、缓存命中率、降级率、P95。

### 5.10 评测体系（贯穿始终）

**数据集**：120 条（W5 100 条 + W8 增补 20 条），5 类：事实、多跳、对比、流程、拒答。每条含：问题、标准答案、参考文档、评分标准、难度。

**指标**

| 层 | 指标 | 目标（示例） |
|---|---|---|
| 检索 | recall@5 / MRR / nDCG@10 | ≥ 0.85 / ≥ 0.75 / ≥ 0.80 |
| 生成 | faithfulness / correctness / citation accuracy | ≥ 0.85 / ≥ 0.80 / ≥ 0.90 |
| Agent | 任务成功率 / 平均步数 / 恢复率 | ≥ 0.80 / ≤ 6 / 1.0 |
| 系统 | P95 首 token / P95 完整 / 错误率 | < 2s / < 8s / < 1% |
| 成本 | 单次会话成本 / 缓存命中 | ≤ ¥0.05 / ≥ 30% |
| 安全 | 注入拦截 / 越权 / PII 泄露 | ≥ 90% / 0 / 0 |

**方法**

- 检索指标用标注的参考文档算，不靠 LLM 猜。
- 生成指标用 LLM-as-judge + 20% 人工抽检校准。
- Agent 用「任务完成定义 + 结果检查」判分，不只看回答。
- 每次优化跑同一套评测集；结果写进 `eval/reports/`。
- CI 门禁：核心指标低于阈值则失败（GitHub Actions）。

**badcase 闭环**：分类 → 归因 → 修复 → 回归 → 记录收益。每周至少修 3 个。

### 5.11 安全与治理（W16）

**威胁模型**

| 威胁 | 例子 | 控制 |
|---|---|---|
| 直接注入 | 用户让模型忽略规则 | 指令层级、输入过滤、输出校验 |
| 间接注入 | 文档/网页/工具返回藏指令 | 内容隔离、工具结果不执行、来源标记 |
| 数据泄露 | 跨租户检索、引用越权 | DB 层租户/ACL 过滤、引用校验 |
| 工具滥用 | 删除/转账/发邮件 | 风险分级、白名单、人工审批、幂等 |
| PII | 手机号/身份证进日志 | 脱敏、日志过滤、保留策略 |
| 成本攻击 | 超长输入/无限循环 | 配额、限流、budget、最大步数 |
| 供应链 | 恶意 MCP server/依赖 | 白名单、签名、版本锁定 |
| 密钥 | Key 进仓库/日志 | 环境变量/密钥管理、扫描 |

**红队 20 用例**：直接注入 5、间接注入 5、越权 4、工具滥用 3、PII 2、成本 1。记录拦截率与修复。

### 5.12 前端（贯穿 W6–W17）

| 页面 | 功能 | 技术点 |
|---|---|---|
| 聊天 | 流式输出、停止、重试、多会话 | SSE、AbortController、乐观更新 |
| 引用 | 来源列表、点击跳转、高亮 | 滚动定位、分栏 |
| 工具时间线 | 调用/结果/耗时/状态 | 折叠、状态机、错误展示 |
| 审批 | 参数展示、批准/拒绝/修改、超时 | 弹窗、轮询/SSE、权限 |
| 文档管理 | 上传、列表、状态、重建索引、ACL | 分页、上传进度、轮询 |
| 评估看板 | 指标趋势、badcase 列表 | 图表（可用轻量库或 SVG） |
| 设置 | 模型、配额、开关 | 表单、校验 |

**原则**：组件库优先（shadcn/ui），Tailwind 布局，不手写复杂 CSS；单次手写 CSS 不超过 30 分钟。

### 5.13 部署与运维（W17）

- Docker Compose：postgres、redis、minio、backend、frontend、parser、langfuse（可选）。
- `.env.example` 完整；一键 `docker compose up -d`。
- 健康检查、日志、指标、告警（简化）。
- 备份：Postgres 每日；MinIO 文档版本。
- CI：构建、单测、Testcontainers 集成测试、评测门禁、镜像构建。
- 演示环境：种子数据 + 演示账号 + 录制视频兜底。

---

## 6. 三次演进的范围与验收

### v1 · RAG 知识库（W6–W9）

**范围**：文档接入、解析、切分、混合检索、rerank、引用、拒答、权限、评估、管理后台、Docker 部署。

**Definition of Done**

- [ ] 120 条评测集可一键跑
- [ ] recall@5 ≥ 0.85、faithfulness ≥ 0.85、引用准确率 ≥ 0.90
- [ ] 权限用例 0 越权
- [ ] P95 首 token < 2s
- [ ] 3 分钟 demo + README 架构图 + 评估报告
- [ ] 有可访问 demo URL（公网或内网），面试可现场打开
- [ ] 干净环境 1 条命令启动

### v2 · Agent Harness（W10–W14）

**范围**：工具平台、MCP、状态图、checkpoint、HITL、记忆、多 Agent、trace、任务评测。

**Definition of Done**

- [ ] 10 个工具、2 个 MCP server 工具
- [ ] 50 任务成功率 ≥ 80%
- [ ] 中断恢复 100%
- [ ] trace 覆盖率 100%，可回放
- [ ] 单任务成本 ≤ ¥0.1
- [ ] 单/多 Agent 对比报告
- [ ] 2 篇深度博客

### v3 · 生产化（W15–W17）

**范围**：模型网关、缓存、限流、配额、压测、成本、安全、多租户、监控、部署、作品集。

**Definition of Done**

- [ ] 50 并发 P95 < 3s、错误率 < 1%
- [ ] 成本 -30% 以上（有对比表）
- [ ] 红队 20 用例拦截 ≥ 90%
- [ ] 多租户隔离测试通过
- [ ] 5 分钟完整演示
- [ ] 简历 + 作品集 + 40 投递

---

## 7. 时间安排（与路线图对齐）

| 周 | 项目任务 | 产出 |
|---|---|---|
| W5 | 立项、评测集、解析原型 | 立项书 + 100 条评测 |
| W6 | 解析、切分、ingestion | pipeline + 切分实验 |
| W7 | embedding、pgvector、混合检索、权限 | retrieval service |
| W8 | rerank、生成、引用、badcase | answer service + citation UI |
| W9 | 管理后台、部署、评估报告、demo | **v1** |
| W10 | 工具平台、MCP、trace | tool platform |
| W11 | 状态图、checkpoint、HITL | workflow |
| W12 | 记忆、上下文 | memory module |
| W13 | 春节缓冲 | 复盘 |
| W14 | 多 Agent、可靠性 | **v2** |
| W15 | 网关、缓存、限流、压测、成本 | 压测/成本报告 |
| W16 | 安全、多租户、红队、简历 | 安全报告 + 简历 |
| W17 | 部署、文档、demo、开源/博客 | **v3** |

---

## 8. 评估报告模板（可直接用）

````markdown
# Atlas 评估报告 v{X} · {日期}

## 1. 数据集
- 版本：v1（120 条）
- 类别分布：事实 40 / 多跳 25 / 对比 20 / 流程 20 / 拒答 15
- 标注方式：人工 + 交叉校验

## 2. 配置
- 模型：主 {model} / 备 {model}
- Embedding：{model}，维度 {dim}
- 检索：pgvector HNSW + BM25，RRF k={k}，topK={k}
- Rerank：{model}，topN={n}
- 切分：{strategy}，size={n}，overlap={n}

## 3. 结果
| 指标 | 基线 | 当前 | 变化 |
|---|---|---|---|
| recall@5 | | | |
| MRR | | | |
| faithfulness | | | |
| citation accuracy | | | |
| P95 首 token | | | |
| 单次成本 | | | |

## 4. Badcase 分析
| 类型 | 数量 | 典型案例 | 修复 |
|---|---|---|---|
| 解析 | | | |
| 切分 | | | |
| 检索 | | | |
| 生成 | | | |

## 5. 结论与下一步
- 最有效的 3 个优化：
- 下一步优先级：
- 已知局限：
```

---

## 9. 简历怎么写（项目 bullet）

> 原则：**动作 + 技术 + 指标 + 业务价值**。每条不超过 2 行，数字必须真实。

**版本 A（AI 应用开发）**

- 主导设计并实现企业级 RAG 知识库 + Agent 工作台（Java 21 / Spring AI / pgvector / Next.js），支持多租户、文档级权限、混合检索与引用溯源；构建 120 条评测集，recall@5 从 0.71 提升至 0.88，faithfulness 0.91。
- 实现 Agent Harness：MCP 工具协议、状态图编排、checkpoint 断点恢复、HITL 审批与记忆模块；50 任务成功率 84%，中断恢复 100%，单任务成本 ≤ ¥0.08。
- 建设模型网关与成本治理：模型路由/降级/语义缓存/租户配额，单次会话成本从 ¥0.13 降至 ¥0.05（-61%），50 并发 P95 < 2.1s。
- 独立交付聊天、引用跳转、工具调用时间线、审批流与管理后台（Next.js / React / SSE），支持流式渲染与错误重试。
- 用 Claude Code / Codex + CLAUDE.md 管理 AI 辅助开发：脚手架、测试、重构均保留 diff review 与测试门禁；v1 到 v3 的交付周期缩短 X%。（按实际填写，不要编）

**版本 B（Java + AI 平台）**

- 基于 Spring Boot 3 + Spring AI 构建企业 AI 能力网关，统一接入 5 家模型，提供路由、降级、灰度、配额与 token 计费；支撑 3 个业务线接入。
- 设计多租户 RAG 服务：pgvector + BM25 混合检索、ACL 过滤、增量索引；P95 检索 < 180ms，越权 0。
- 用虚拟线程 + SSE + 多级缓存优化高并发问答，50 并发 P95 < 2.1s，错误率 < 0.5%。

**版本 C（Agent 开发）**

- 设计并实现可恢复的 Agent 工作流：状态图 + checkpoint + HITL + 工具沙箱，支持审批中断后从断点恢复，恢复成功率 100%。
- 接入 MCP 协议，将内部工单/库存/订单系统封装为 10 个工具，按风险分级授权；工具调用成功率 96%。
- 构建 Agent 评测体系：50 任务集、成功率/成本/延迟指标、trace 回放；多 Agent 相比单 Agent 成功率 +12%，成本 +35%，据此选择混合策略。

> 面试时每个数字都要能解释：怎么测的、基线是什么、分子分母是什么。**编数字是自杀**。

---

## 10. 面试怎么讲（3 / 10 / 30 分钟）

### 3 分钟版（电梯陈述）

1. **背景**：企业文档散落、支持工程师找答案慢、跨系统操作多。
2. **方案**：RAG + Agent 工作台，Java 后端 + Next.js 前端，多租户、权限、引用、审批。
3. **结果**：recall@5 0.88、faithfulness 0.91、任务成功率 84%、成本 -61%、P95 < 2.1s。
4. **取舍**：为什么 pgvector、为什么状态图、为什么 MCP、为什么多 Agent 只用在部分场景。
5. **反思**：如果重做，会先做评测集、会早做成本核算、会砍掉哪些花活。

### 10 分钟版（加架构与评测）

- 架构图逐层讲：前端 → API → RAG/Agent/网关 → 存储/模型。
- 数据流：上传 → 解析 → 切分 → 索引；提问 → 检索 → rerank → 生成 → 引用。
- 评测：数据集、指标、baseline vs 优化、badcase 闭环。
- 故障：一次真实事故（如权限泄漏/模型超时/索引不一致）怎么发现、怎么修、怎么防。

### 30 分钟版（深挖 + 取舍）

每个模块准备 3 层：**怎么做 → 为什么 → 代价/替代**。例如检索：

1. 怎么做：pgvector HNSW + BM25 + RRF + rerank。
2. 为什么：中文关键词强、向量语义强；RRF 不需调权重；rerank 提升 top 精度。
3. 代价：索引体积 +35%、rerank 延迟 +80ms、复杂度上升；数据量 > 千万换 Milvus。

MCP 也可以这样讲：

1. 怎么做：2026-07-28 无状态规范，server 暴露 tools，client `server/discover` 后发现并调用，MRTR 承载审批。
2. 为什么：N×M 接入变 N+M；无状态对网关/负载均衡友好；审批可协议化。
3. 代价：旧教程/旧 SDK 不兼容、安全边界要自己补（白名单、权限、审计）；框架支持要实测。

### 5 层追问示例（提前准备）

1. 为什么 recall@5 是 0.88？怎么算的？
2. 评测集怎么构造？会不会过拟合？
3. 哪个优化贡献最大？怎么证明？
4. 线上真实分布和评测集不一致怎么办？
5. 如果预算减半，你会砍哪个模块？

**MCP 专项追问**：MCP 2026-07-28 为什么去掉 session/initialize？`server/discover` 解决什么？MRTR 和 Function Calling 的确认机制怎么配合？

---

## 11. README 模板

```markdown
# Atlas · 企业知识库 + Agent 工作台

> 一句话：面向企业支持团队的多租户 RAG + Agent 平台，支持引用溯源、工具调用、人工审批与成本治理。

![demo](docs/demo.gif)

## 功能
- 文档接入 / 解析 / 切分 / 增量索引
- 混合检索 + rerank + 引用 + 拒答
- 多租户 / 文档级 ACL / 审计
- Agent 状态图 / MCP 工具 / checkpoint / HITL
- 记忆 / 多 Agent / trace / 成本看板
- Next.js 前端：聊天、引用、工具时间线、审批、管理后台

## 架构
（图）

## 快速开始
```bash
cp .env.example .env
docker compose up -d
# 访问 http://localhost:3000
```

## 评测结果
| 指标 | 基线 | 当前 |
...

## 设计决策
- 为什么 pgvector：...
- 为什么状态图：...
- 为什么 MCP：...

## 已知局限
- ...

## Roadmap
- ...
````

---

## 12. 时间不够时砍什么

**砍的顺序**（从下往上）：

1. 多 Agent 花活（保留 supervisor 单层）
2. K8s / 高级部署
3. OCR / 复杂表格
4. 管理后台高级统计
5. 语义缓存（保留精确缓存）
6. 前端动画/美化

**绝不砍**：

- 评测集与指标
- 引用与权限
- 状态图 + HITL
- 成本报告
- demo 视频与 README
- 投递时间

---

## 13. 常见坑

| 坑 | 后果 | 避免 |
|---|---|---|
| 先写框架再写需求 | 做了个没人用的平台 | 先定用户/场景/评测 |
| 评测集最后才做 | 无法证明优化有效 | W5 冻结评测集 |
| 追 SOTA 模型 | 频繁重写，没沉淀 | 模型可替换，评测集不变 |
| 忽视权限 | 企业场景一票否决 | DB 层过滤 + 越权测试 |
| 多 Agent 上头 | 成本爆炸、调试困难 | 先证明单 Agent 不够 |
| 前端完美主义 | 挤占核心时间 | 组件库 + 30 分钟 CSS 上限 |
| demo 依赖本地 | 面试现场翻车 | 干净环境验收 + 录屏兜底 |
| 不记决策 | 面试问「为什么」答不出 | 每周决策日志 |
| 学过时 MCP 教程 | 一开口就暴露信息陈旧 | 只读 2026-07-28 官方规范；旧教程只作历史 |
| 不做成本核算 | 无法讲工程价值 | 从第一天记 token/成本 |
| 数据隐私 | 真实文档泄露 | 脱敏 + 本地/私有化 + 权限 |

---

## 14. 项目完成后的资产清单

- [ ] GitHub 仓库（README、架构图、评测报告、部署文档）
- [ ] 3 分钟 demo 视频
- [ ] 在线 demo（可选）
- [ ] 120 条评测集 + 跑分脚本
- [ ] 6–8 篇博客（每篇一个技术点）
- [ ] 决策日志 20+ 条
- [ ] 简历 3 版 bullet
- [ ] 3/10/30 分钟讲述稿
- [ ] 5 层追问清单
- [ ] 故障/优化案例 3 个

> 这些资产本身就是你 22 周学习的产品。**项目不是作业，是你的求职产品。**
