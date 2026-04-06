import { useNavigate } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'

interface Props {
  username: string | null
  onLogout: () => void
}

export default function Navbar({ username, onLogout }: Props) {
  const navigate = useNavigate()
  const { theme, toggle } = useTheme()
  const isDark = theme === 'dark'

  function handleLogout() {
    onLogout()
    navigate('/login', { replace: true })
  }

  return (
    <nav className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        <a href="/" className="text-blue-600 dark:text-blue-400 font-extrabold text-lg whitespace-nowrap tracking-tight">
          🚗 Million Miles
        </a>
        <div className="flex items-center gap-4">
          {username && (
            <span className="hidden sm:block text-sm text-gray-500 dark:text-gray-400">
              Hi, <span className="font-semibold text-gray-700 dark:text-gray-200">{username}</span>
            </span>
          )}

          {/* iOS-style dark mode toggle */}
          <button
            onClick={toggle}
            aria-label="Toggle dark mode"
            className="flex items-center gap-1.5 select-none"
          >
            {/* Sun icon */}
            <svg className={`w-4 h-4 transition-colors ${isDark ? 'text-gray-500' : 'text-yellow-400'}`}
              fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 4.5a.75.75 0 0 1 .75.75v1.5a.75.75 0 0 1-1.5 0v-1.5A.75.75 0 0 1 12 4.5ZM18.364 6.343a.75.75 0 0 1 0 1.06l-1.06 1.061a.75.75 0 1 1-1.06-1.06l1.06-1.061a.75.75 0 0 1 1.06 0ZM19.5 12a.75.75 0 0 1-.75.75h-1.5a.75.75 0 0 1 0-1.5h1.5A.75.75 0 0 1 19.5 12ZM17.303 17.303a.75.75 0 0 1-1.06 0l-1.061-1.06a.75.75 0 1 1 1.06-1.06l1.061 1.06a.75.75 0 0 1 0 1.06ZM12 19.5a.75.75 0 0 1-.75-.75v-1.5a.75.75 0 0 1 1.5 0v1.5A.75.75 0 0 1 12 19.5ZM6.697 17.303a.75.75 0 0 1 0-1.06l1.06-1.061a.75.75 0 0 1 1.06 1.06l-1.06 1.061a.75.75 0 0 1-1.06 0ZM4.5 12a.75.75 0 0 1 .75-.75h1.5a.75.75 0 0 1 0 1.5h-1.5A.75.75 0 0 1 4.5 12ZM6.697 6.343a.75.75 0 0 1 1.06 0l1.061 1.06a.75.75 0 0 1-1.06 1.061L6.697 7.404a.75.75 0 0 1 0-1.06ZM12 8.25a3.75 3.75 0 1 0 0 7.5 3.75 3.75 0 0 0 0-7.5Z"/>
            </svg>

            {/* Track */}
            <span className={`relative inline-flex w-11 h-6 rounded-full transition-colors duration-300 ${isDark ? 'bg-blue-600' : 'bg-gray-300'}`}>
              {/* Thumb */}
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-300 ${isDark ? 'translate-x-5' : 'translate-x-0'}`} />
            </span>

            {/* Moon icon */}
            <svg className={`w-4 h-4 transition-colors ${isDark ? 'text-blue-400' : 'text-gray-400'}`}
              fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" d="M9.528 1.718a.75.75 0 0 1 .162.819A8.97 8.97 0 0 0 9 6a9 9 0 0 0 9 9 8.97 8.97 0 0 0 3.463-.69.75.75 0 0 1 .981.98 10.503 10.503 0 0 1-9.694 6.46c-5.799 0-10.5-4.7-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 0 1 .818.162Z" clipRule="evenodd"/>
            </svg>
          </button>

          <button
            onClick={handleLogout}
            className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition font-medium"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  )
}
