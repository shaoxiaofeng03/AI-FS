import { defineConfig } from 'vitepress'

// GitHub Pages 项目站点地址是 https://<user>.github.io/<repo>/，
// 构建时必须用仓库名作为 base，否则 CSS/JS 会 404。
// 部署工作流会注入 BASE_PATH；本地开发默认 '/'。
// 绑定自定义域名后，把仓库变量 BASE_PATH 设为 '/' 即可。
const BASE = process.env.BASE_PATH || '/'

export default defineConfig({
  lang: 'zh-CN',
  title: 'AI 全栈 22 周作战包',
  description: 'Java 后端 → AI 应用 / Agent 全栈 · 22 周学习路线、每日打卡、项目与面试作战',
  base: BASE,

  // 以仓库根目录为站点源：README / DECISIONS / ERRORS / docs / research 都能进站
  srcDir: '.',
  srcExclude: [
    'checkin/**',
    'tracker/**',
    'plan/**',
    'scripts/**',
    'public/**',
    'node_modules/**',
    '.github/**',
    '.vitepress/**',
    '.git/**',
    'pnpm-lock.yaml',
    'package-lock.json'
  ],

  // 文档里会链接到 data / checkin / 本地文件；首次部署先不阻断构建
  ignoreDeadLinks: true,
  // GitHub Pages 对无扩展名 URL 的兼容性不稳定，这里保留 .html，确保静态托管可直接访问
  cleanUrls: false,
  lastUpdated: true,
  publicDir: 'public',

  head: [
    ['meta', { name: 'theme-color', content: '#4f46e5' }],
    ['meta', { name: 'mobile-web-app-capable', content: 'yes' }]
  ],

  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '路线图', link: '/docs/01-学习路线图' },
      { text: '每周执行', link: '/docs/02-每周执行手册' },
      { text: '打卡系统', link: '/docs/03-每日打卡与精进系统' },
      { text: '在线看板', link: '/docs/09-在线工具' },
      { text: '部署', link: '/GITHUB_PAGES' }
    ],

    sidebar: [
      {
        text: '开始',
        items: [
          { text: '首页', link: '/' },
          { text: 'README 总览', link: '/README' },
          { text: 'GitHub Pages 部署', link: '/GITHUB_PAGES' }
        ]
      },
      {
        text: '22 周计划',
        items: [
          { text: '00 · 目标与策略', link: '/docs/00-目标与策略' },
          { text: '01 · 学习路线图', link: '/docs/01-学习路线图' },
          { text: '02 · 每周执行手册', link: '/docs/02-每周执行手册' },
          { text: '03 · 每日打卡与精进系统', link: '/docs/03-每日打卡与精进系统' }
        ]
      },
      {
        text: '项目与求职',
        items: [
          { text: '04 · 旗舰项目 Atlas', link: '/docs/04-旗舰项目Atlas' },
          { text: '05 · 面试与求职作战', link: '/docs/05-面试与求职作战' }
        ]
      },
      {
        text: '方法与资料',
        items: [
          { text: '06 · 专家方法与工具', link: '/docs/06-专家方法与工具' },
          { text: '07 · 文档生成方法', link: '/docs/07-文档生成方法' },
          { text: '08 · 资源清单', link: '/docs/08-资源清单' },
          { text: '10 · 分阶段知识清单与资源', link: '/docs/10-分阶段知识清单与学习资源' }
        ]
      },
      {
        text: '在线工具',
        items: [
          { text: '09 · 打卡与看板', link: '/docs/09-在线工具' },
          { text: 'DECISIONS 决策日志', link: '/DECISIONS' },
          { text: 'ERRORS 错题本', link: '/ERRORS' }
        ]
      },
      {
        text: '调研',
        items: [
          { text: '2026-11 市场与技术调研', link: '/research/2026-市场与技术调研' }
        ]
      }
    ],

    search: { provider: 'local' },

    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '目录',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色',
    darkModeSwitchTitle: '切换到深色',

    footer: {
      message: 'VitePress 构建 · GitHub Pages 自动部署 · 数据默认存本机浏览器',
      copyright: 'AI 全栈 22 周作战包'
    }
  }
})
