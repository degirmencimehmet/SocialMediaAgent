import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { api } from '../api/client'
import StatCard from '../components/StatCard'

const TENANT = 'hotel_001'
const COLORS = ['#6366F1', '#10B981', '#EF4444', '#F59E0B']

export default function Analytics() {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getAnalytics(TENANT)
      .then(setAnalytics)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-gray-400">Yükleniyor...</div>
  if (!analytics) return <div className="p-8 text-gray-400">Veri yok.</div>

  const pieData = [
    { name: 'Onaylı', value: analytics.approved_posts - analytics.published_posts },
    { name: 'Yayında', value: analytics.published_posts },
    { name: 'Reddedildi', value: analytics.rejected_posts },
    { name: 'Bekliyor', value: analytics.total_posts - analytics.approved_posts - analytics.rejected_posts },
  ].filter(d => d.value > 0)

  const engagementData = [
    { name: 'Beğeni', value: analytics.avg_likes },
    { name: 'Erişim', value: analytics.avg_reach },
    { name: 'Yorum', value: analytics.avg_comments },
  ]

  return (
    <div className="p-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Analitik</h2>
        <p className="text-sm text-gray-500 mt-0.5">Kampanya performansı</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard title="Toplam İçerik" value={analytics.total_posts} color="indigo" />
        <StatCard title="Onay Oranı" value={`%${analytics.approval_rate}`} color="green" />
        <StatCard title="Ort. Beğeni" value={analytics.avg_likes.toFixed(1)} color="yellow" />
        <StatCard title="Ort. Erişim" value={analytics.avg_reach.toFixed(1)} color="indigo" />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Status distribution */}
        <div className="card p-5">
          <h3 className="font-semibold text-gray-700 mb-4">İçerik Durumu</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-gray-400 text-sm">
              Henüz veri yok
            </div>
          )}
        </div>

        {/* Engagement metrics */}
        <div className="card p-5">
          <h3 className="font-semibold text-gray-700 mb-4">Ortalama Etkileşim</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={engagementData} barSize={40}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#6366F1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Info box */}
      <div className="mt-6 bg-indigo-50 rounded-xl p-4 text-sm text-indigo-700">
        <strong>Not:</strong> Etkileşim verileri Meta Graph API aracılığıyla toplanır.
        API bağlantısı yapılandırılmadan veriler sıfır görünür.
      </div>
    </div>
  )
}
