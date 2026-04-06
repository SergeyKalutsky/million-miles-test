import { useNavigate } from 'react-router-dom'

interface Props {
  username: string | null
  onLogout: () => void
}

export default function Navbar({ username, onLogout }: Props) {
  const navigate = useNavigate()

  function handleLogout() {
    onLogout()
    navigate('/login', { replace: true })
  }

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        <a href="/" className="text-blue-700 font-extrabold text-lg whitespace-nowrap tracking-tight">
          🚗 Million Miles
        </a>
        <div className="flex items-center gap-3">
          {username && (
            <span className="hidden sm:block text-sm text-gray-500">
              Hi, <span className="font-semibold text-gray-700">{username}</span>
            </span>
          )}
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  )
}
