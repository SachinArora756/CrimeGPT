import { Bell, Search } from 'lucide-react'

export default function Header() {
  return (
    <header className="h-16 bg-dark-900 border-b border-dark-700 flex items-center justify-between px-6">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            type="text"
            placeholder="Search cases, FIR numbers..."
            className="input pl-10 py-2 text-sm"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button className="relative p-2 text-dark-400 hover:text-white transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-primary-500 rounded-full"></span>
        </button>
      </div>
    </header>
  )
}
