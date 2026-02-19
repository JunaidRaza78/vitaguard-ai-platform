import { create } from 'zustand'

const useThemeStore = create((set) => ({
  isDark: localStorage.getItem('theme') !== 'light',
  toggle: () =>
    set((state) => {
      const next = !state.isDark
      localStorage.setItem('theme', next ? 'dark' : 'light')
      document.documentElement.classList.toggle('light-mode', !next)
      return { isDark: next }
    }),
}))

export default useThemeStore
