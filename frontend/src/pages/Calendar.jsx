import { useState, useEffect } from 'react'
import { format, getDaysInMonth, startOfMonth, getDay } from 'date-fns'
import { tr } from 'date-fns/locale'
import { ChevronLeft, ChevronRight, Download } from 'lucide-react'
import { api } from '../api/client'

const TENANT = 'hotel_001'
const STATUS_COLORS = {
  approved:  'bg-green-100 text-green-700 border-green-200',
  published: 'bg-blue-100 text-blue-700 border-blue-200',
  pending:   'bg-yellow-100 text-yellow-700 border-yellow-200',
}

export default function Calendar() {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)

  const loadCalendar = async () => {
    setLoading(true)
    try {
      const data = await api.getCalendar(TENANT, year, month)
      setEntries(data.entries || [])
    } catch (e) {
      setEntries([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadCalendar() }, [year, month])

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear(y => y - 1) }
    else setMonth(m => m - 1)
  }
  const nextMonth = () => {
    if (month === 12) { setMonth(1); setYear(y => y + 1) }
    else setMonth(m => m + 1)
  }

  // Build calendar grid
  const daysInMonth = getDaysInMonth(new Date(year, month - 1))
  const firstDayOfWeek = (getDay(startOfMonth(new Date(year, month - 1))) + 6) % 7  // Mon=0
  const cells = Array.from({ length: firstDayOfWeek }).fill(null).concat(
    Array.from({ length: daysInMonth }, (_, i) => i + 1)
  )

  const entriesByDay = {}
  entries.forEach(e => {
    if (!e.scheduled_time) return
    const d = new Date(e.scheduled_time).getDate()
    if (!entriesByDay[d]) entriesByDay[d] = []
    entriesByDay[d].push(e)
  })

  const monthLabel = format(new Date(year, month - 1), 'MMMM yyyy', { locale: tr })
  const pdfUrl = api.getCalendarPdfUrl(TENANT, year, month)
  const jsonUrl = api.getCalendarJsonUrl(TENANT, year, month)

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">İçerik Takvimi</h2>
          <p className="text-sm text-gray-500 mt-0.5">Aylık yayın planı</p>
        </div>
        <div className="flex items-center gap-2">
          <a href={pdfUrl} target="_blank" rel="noreferrer"
            className="btn-secondary flex items-center gap-1.5 text-xs">
            <Download size={13} /> PDF
          </a>
          <a href={jsonUrl} target="_blank" rel="noreferrer"
            className="btn-secondary flex items-center gap-1.5 text-xs">
            <Download size={13} /> JSON
          </a>
        </div>
      </div>

      {/* Month navigator */}
      <div className="card p-4 mb-6">
        <div className="flex items-center justify-between">
          <button onClick={prevMonth} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
            <ChevronLeft size={18} />
          </button>
          <h3 className="font-semibold text-gray-800 capitalize">{monthLabel}</h3>
          <button onClick={nextMonth} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* Calendar grid */}
      <div className="card overflow-hidden">
        {/* Day headers */}
        <div className="grid grid-cols-7 border-b border-gray-200 bg-gray-50">
          {['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'].map(d => (
            <div key={d} className="py-2 text-center text-xs font-medium text-gray-500">{d}</div>
          ))}
        </div>

        {/* Day cells */}
        <div className="grid grid-cols-7">
          {cells.map((day, i) => {
            const dayEntries = day ? (entriesByDay[day] || []) : []
            return (
              <div
                key={i}
                className={`min-h-[100px] p-2 border-b border-r border-gray-100 ${!day ? 'bg-gray-50' : ''}`}
              >
                {day && (
                  <>
                    <span className={`text-xs font-medium ${
                      day === now.getDate() && month === now.getMonth() + 1 && year === now.getFullYear()
                        ? 'bg-indigo-600 text-white w-5 h-5 rounded-full flex items-center justify-center'
                        : 'text-gray-500'
                    }`}>
                      {day}
                    </span>
                    <div className="mt-1 space-y-1">
                      {dayEntries.slice(0, 2).map(e => (
                        <div
                          key={e.post_id}
                          className={`text-xs px-1.5 py-0.5 rounded border truncate ${STATUS_COLORS[e.status] || STATUS_COLORS.pending}`}
                          title={e.caption_preview}
                        >
                          {e.platform.slice(0, 2).toUpperCase()} · {e.caption_preview.slice(0, 20)}…
                        </div>
                      ))}
                      {dayEntries.length > 2 && (
                        <span className="text-xs text-gray-400">+{dayEntries.length - 2} daha</span>
                      )}
                    </div>
                  </>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-100 border border-green-200 inline-block"/> Onaylı</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-100 border border-blue-200 inline-block"/> Yayınlandı</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-yellow-100 border border-yellow-200 inline-block"/> Bekliyor</span>
      </div>
    </div>
  )
}
