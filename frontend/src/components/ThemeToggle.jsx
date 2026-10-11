import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export default function ThemeToggle({ className = 'nav-logout' }) {
  const { theme, toggle, isDark } = useTheme()
  return (
    <button
      className={className}
      onClick={toggle}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-pressed={isDark}
    >
      {isDark ? <Sun size={17} /> : <Moon size={17} />}
    </button>
  )
}
