<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { withBase } from 'vitepress'

const STORAGE_KEY = 'atlas-tracker-v1'
const DAY_CN = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
const WEEKDAY_HOURS = [4, 2, 2, 2, 2, 2, 6] // 周日..周六

const ready = ref(false)
const loadError = ref('')
const plan = ref(null)
const now = ref(new Date())
const checks = ref({ outcomes: [], eval: [], output: false })
const todayRecord = ref(null)
let timer = null

function pad2(n) { return String(n).padStart(2, '0') }
function dateKey(d) { return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}` }
function parseKey(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '')
  if (!m) return null
  return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
}
function dayNum(d) {
  return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86400000)
}

const weeks = computed(() => (plan.value?.weeks || []).slice().sort((a, b) => a.week - b.week))
const phases = computed(() => {
  const map = {}
  for (const p of plan.value?.phases || []) map[p.id] = p
  return map
})

const currentWeek = computed(() => {
  if (!weeks.value.length) return null
  const n = dayNum(now.value)
  for (const w of weeks.value) {
    const s = parseKey(w.start)
    const e = parseKey(w.end)
    if (s && e && n >= dayNum(s) && n <= dayNum(e)) return { week: w, status: 'active', days: 0 }
  }
  const first = weeks.value[0]
  const firstStart = parseKey(first.start)
  if (firstStart && n < dayNum(firstStart)) {
    return { week: first, status: 'before', days: dayNum(firstStart) - n }
  }
  return { week: weeks.value[weeks.value.length - 1], status: 'after', days: 0 }
})

const week = computed(() => currentWeek.value?.week || null)
const weekNo = computed(() => week.value?.week || 0)
const phase = computed(() => phases.value[week.value?.phase] || { id: '', name: '', goal: '' })
const weekday = computed(() => now.value.getDay())

const todayFocus = computed(() => {
  if (!week.value) return ''
  if (currentWeek.value.status === 'before') {
    return `计划还有 ${currentWeek.value.days} 天开始：先做 W1 预热（读概念 + 跑通第一条链路）`
  }
  if (currentWeek.value.status === 'after') {
    return '22 周计划已结束：复盘资产、继续投递、准备入职'
  }
  if (weekday.value === 0) return '周日复盘：逐条验收 Eval、发布产出、写周复盘 + 定下周三件事'
  if (weekday.value === 6) return `项目深度块：${week.value.project}（3 × 90min，不切任务）`
  const i = weekday.value - 1
  return week.value.outcomes?.[i] || `推进项目：${week.value.project}`
})

const todayHours = computed(() => {
  if (currentWeek.value.status === 'before') return 2
  return WEEKDAY_HOURS[weekday.value] ?? 2
})

const dateLabel = computed(() => {
  const d = now.value
  return `${d.getMonth() + 1}/${d.getDate()} ${DAY_CN[d.getDay()]}`
})

const totalTasks = computed(() => {
  if (!week.value) return 0
  return (week.value.outcomes?.length || 0) + (week.value.eval?.length || 0) + 1
})
const doneTasks = computed(() => {
  const o = checks.value.outcomes || []
  const e = checks.value.eval || []
  return o.filter(Boolean).length + e.filter(Boolean).length + (checks.value.output ? 1 : 0)
})
const progressPct = computed(() => totalTasks.value ? Math.round((doneTasks.value / totalTasks.value) * 100) : 0)

const trackerHref = computed(() => withBase('/tracker/'))
const manualHref = computed(() => withBase('/docs/02-每周执行手册.html'))
const knowledgeHref = computed(() => withBase('/docs/10-分阶段知识清单与学习资源.html'))
const notesHref = computed(() => {
  if (weekNo.value <= 2) return withBase('/docs/notes/W1-大模型核心概念速记.html')
  return ''
})
const pythonNotesHref = computed(() => {
  if (weekNo.value <= 2) return withBase('/docs/notes/W1-Python够用线教程.html')
  return ''
})

function readStore() {
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

function loadChecks() {
  if (!week.value) return
  const raw = readStore()
  const c = raw?.checks?.[String(weekNo.value)] || {}
  checks.value = {
    outcomes: (week.value.outcomes || []).map((_, i) => c.outcomes?.[i] === true),
    eval: (week.value.eval || []).map((_, i) => c.eval?.[i] === true),
    output: c.output === true
  }
  const rec = raw?.records?.[dateKey(now.value)]
  todayRecord.value = rec && Number(rec.hours) > 0 ? rec : null
}

function saveChecks() {
  try {
    const raw = readStore()
    raw.version = raw.version || 1
    raw.records = raw.records || {}
    raw.checks = raw.checks || {}
    raw.checks[String(weekNo.value)] = {
      outcomes: checks.value.outcomes,
      eval: checks.value.eval,
      output: checks.value.output
    }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(raw))
  } catch {
    loadError.value = '本地存储不可用，勾选只在本次页面有效。'
  }
}

function toggle(kind, index) {
  if (kind === 'output') checks.value.output = !checks.value.output
  else checks.value[kind][index] = !checks.value[kind][index]
  saveChecks()
}

async function loadPlan() {
  try {
    const res = await fetch(withBase('/plan/plan.json'), { cache: 'no-store' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    plan.value = await res.json()
    if (!plan.value?.weeks?.length) throw new Error('plan.json 没有 weeks')
    loadChecks()
    ready.value = true
  } catch (err) {
    loadError.value = `读取计划失败：${err.message}`
    ready.value = true
  }
}

function refreshNow() {
  now.value = new Date()
  if (ready.value) loadChecks()
}

function onStorage(event) {
  if (event.key === STORAGE_KEY) loadChecks()
}

onMounted(() => {
  loadPlan()
  timer = window.setInterval(refreshNow, 60_000)
  window.addEventListener('storage', onStorage)
  document.addEventListener('visibilitychange', refreshNow)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
  window.removeEventListener('storage', onStorage)
  document.removeEventListener('visibilitychange', refreshNow)
})
</script>

<template>
  <section class="today-panel" v-if="ready && plan && week">
    <div class="tp-top">
      <div class="tp-week">
        <span class="tp-kicker">当前任务</span>
        <strong>第 {{ weekNo }} 周</strong>
        <span class="tp-muted">/ 共 {{ weeks.length }} 周</span>
      </div>
      <div class="tp-meta">
        <span>{{ dateLabel }}</span>
        <span v-if="currentWeek.status === 'before'" class="tp-pill">还有 {{ currentWeek.days }} 天开始</span>
        <span v-else-if="currentWeek.status === 'after'" class="tp-pill">计划已结束</span>
        <span v-else class="tp-pill tp-live">进行中</span>
      </div>
    </div>

    <div class="tp-headline">
      <div>
        <h2>{{ week.theme }}</h2>
        <p class="tp-sub">{{ phase.id }} · {{ phase.name }} ｜ {{ week.start }} ~ {{ week.end }}</p>
      </div>
      <div class="tp-progress">
        <div class="tp-progress-num">{{ doneTasks }}<span>/{{ totalTasks }}</span></div>
        <div class="tp-bar"><i :style="{ width: progressPct + '%' }"></i></div>
        <div class="tp-muted">本周完成 {{ progressPct }}%</div>
      </div>
    </div>

    <div class="tp-grid">
      <div class="tp-card tp-today">
        <div class="tp-label">今天任务</div>
        <h3>{{ todayFocus }}</h3>
        <p class="tp-muted">建议投入 {{ todayHours }}h ｜ 本周项目：{{ week.project }}</p>
        <p class="tp-checkin">
          <template v-if="todayRecord">✅ 今天已打卡 {{ todayRecord.hours }}h</template>
          <template v-else>○ 今天还没打卡</template>
        </p>
        <a class="tp-btn" :href="trackerHref">打开打卡看板 →</a>
      </div>

      <div class="tp-card">
        <div class="tp-label">本周要完成</div>
        <ul class="tp-tasks">
          <li v-for="(o, i) in week.outcomes" :key="'o' + i">
            <label>
              <input type="checkbox" :checked="checks.outcomes[i]" @change="toggle('outcomes', i)" />
              <span>{{ o }}</span>
            </label>
          </li>
          <li v-for="(e, i) in week.eval" :key="'e' + i">
            <label>
              <input type="checkbox" :checked="checks.eval[i]" @change="toggle('eval', i)" />
              <span>验收：{{ e }}</span>
            </label>
          </li>
          <li>
            <label>
              <input type="checkbox" :checked="checks.output" @change="toggle('output')" />
              <span>产出：{{ week.output }}</span>
            </label>
          </li>
        </ul>
      </div>

      <div class="tp-card">
        <div class="tp-label">当下要看的资料</div>
        <ul class="tp-links">
          <li>
            <a :href="manualHref">02 · 本周执行手册</a>
            <span>每天 2h 的具体动作</span>
          </li>
          <li>
            <a :href="knowledgeHref">10 · 本阶段知识清单</a>
            <span>知识点 + 文档/视频 + 自测</span>
          </li>
          <li v-if="notesHref">
            <a :href="notesHref">W1 · 大模型概念速记</a>
            <span>先背 §0，再做 15 题</span>
          </li>
          <li v-if="pythonNotesHref">
            <a :href="pythonNotesHref">W1 · Python 够用线</a>
            <span>按 §0 三轮走，6h</span>
          </li>
          <li>
            <a :href="trackerHref">打卡看板 / 云端同步</a>
            <span>记录小时、连续天数、22 周进度</span>
          </li>
        </ul>
      </div>
    </div>

    <p v-if="loadError" class="tp-error">{{ loadError }}</p>
  </section>

  <section class="today-panel tp-loading" v-else>
    <span v-if="loadError">{{ loadError }}</span>
    <span v-else>正在读取计划与今日任务…</span>
  </section>
</template>

<style scoped>
.today-panel {
  margin: 28px auto 8px;
  padding: 22px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 16px;
  background: var(--vp-c-bg-soft);
}
.tp-loading { color: var(--vp-c-text-2); text-align: center; }
.tp-top { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; align-items: center; }
.tp-week { display: flex; align-items: baseline; gap: 8px; }
.tp-kicker { font-size: 12px; letter-spacing: .08em; color: var(--vp-c-brand-1); font-weight: 700; }
.tp-week strong { font-size: 22px; }
.tp-muted { color: var(--vp-c-text-2); font-size: 13px; }
.tp-meta { display: flex; gap: 8px; align-items: center; font-size: 13px; color: var(--vp-c-text-2); }
.tp-pill { border: 1px solid var(--vp-c-divider); border-radius: 999px; padding: 2px 10px; font-size: 12px; }
.tp-live { color: #047857; border-color: #a7f3d0; background: #ecfdf5; }
.tp-headline { display: flex; justify-content: space-between; gap: 24px; flex-wrap: wrap; margin: 14px 0 18px; }
.tp-headline h2 { margin: 0 0 4px; font-size: 24px; }
.tp-sub { margin: 0; color: var(--vp-c-text-2); font-size: 13px; }
.tp-progress { min-width: 180px; text-align: right; }
.tp-progress-num { font-size: 26px; font-weight: 700; line-height: 1.1; }
.tp-progress-num span { font-size: 14px; color: var(--vp-c-text-2); font-weight: 500; }
.tp-bar { height: 8px; background: var(--vp-c-default-soft); border-radius: 999px; overflow: hidden; margin: 6px 0 4px; }
.tp-bar i { display: block; height: 100%; background: var(--vp-c-brand-1); border-radius: 999px; transition: width .25s; }
.tp-grid { display: grid; grid-template-columns: 1.05fr 1.2fr 1fr; gap: 14px; }
.tp-card { background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 12px; padding: 16px; min-width: 0; }
.tp-label { font-size: 12px; font-weight: 700; color: var(--vp-c-brand-1); letter-spacing: .06em; margin-bottom: 8px; }
.tp-today h3 { margin: 0 0 8px; font-size: 17px; line-height: 1.5; }
.tp-checkin { margin: 8px 0 12px; font-size: 13px; color: var(--vp-c-text-2); }
.tp-btn { display: inline-block; background: var(--vp-c-brand-1); color: var(--vp-c-bg) !important; border-radius: 8px; padding: 7px 12px; font-size: 13px; font-weight: 600; text-decoration: none; }
.tp-tasks, .tp-links { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.tp-tasks li label { display: flex; gap: 8px; align-items: flex-start; font-size: 13.5px; line-height: 1.55; cursor: pointer; }
.tp-tasks input { margin-top: 2px; flex: none; }
.tp-links li { display: flex; flex-direction: column; gap: 1px; }
.tp-links a { font-size: 13.5px; font-weight: 600; text-decoration: none; }
.tp-links span { font-size: 12px; color: var(--vp-c-text-2); }
.tp-error { margin: 12px 0 0; color: var(--vp-c-danger-1); font-size: 13px; }
.dark .tp-live { background: rgba(16, 185, 129, .12); color: #6ee7b7; border-color: rgba(16, 185, 129, .35); }
@media (max-width: 960px) {
  .tp-grid { grid-template-columns: 1fr; }
  .tp-progress { text-align: left; }
}
</style>
