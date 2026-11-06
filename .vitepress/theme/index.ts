import DefaultTheme from 'vitepress/theme'
import TodayPanel from './components/TodayPanel.vue'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('TodayPanel', TodayPanel)
  }
}
