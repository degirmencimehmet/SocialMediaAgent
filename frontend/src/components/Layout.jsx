import { NavLink } from 'react-router-dom'
import { LayoutDashboard, CalendarDays, BarChart3, Settings } from 'lucide-react'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/calendar', label: 'Takvim', icon: CalendarDays },
  { to: '/analytics', label: 'Analitik', icon: BarChart3 },
  { to: '/settings', label: 'Ayarlar', icon: Settings },
]

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🤖</span>
            <div>
              <h1 className="font-bold text-gray-900 text-sm leading-tight">AI Sosyal Medya</h1>
              <p className="text-xs text-gray-500">Turizm Asistanı</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <div className="bg-indigo-50 rounded-lg p-3 text-xs text-indigo-700">
            <p className="font-medium mb-1">Telegram Bağlantısı</p>
            <p className="text-indigo-600">Onay bildirimleri Telegram üzerinden gelir</p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
