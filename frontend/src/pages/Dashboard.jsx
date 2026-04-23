import { useState, useEffect } from 'react'
import { Sparkles, RefreshCw } from 'lucide-react'
import { api } from '../api/client'
import PostCard from '../components/PostCard'
import StatCard from '../components/StatCard'

const TENANT = 'hotel_001'

export default function Dashboard() {
  const [posts, setPosts] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [prompt, setPrompt] = useState('')
  const [platform, setPlatform] = useState('instagram')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadData = async () => {
    setLoading(true)
    try {
      const [postsData, analyticsData] = await Promise.all([
        api.getPosts({ tenant_id: TENANT, limit: 20 }),
        api.getAnalytics(TENANT),
      ])
      setPosts(postsData)
      setAnalytics(analyticsData)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleGenerate = async (e) => {
    e.preventDefault()
    if (!prompt.trim()) return
    setGenerating(true)
    setError('')
    setSuccess('')
    try {
      const post = await api.generatePost({ tenant_id: TENANT, prompt, platform })
      setPosts(prev => [post, ...prev])
      setSuccess('İçerik oluşturuldu! Telegram\'dan onaylayabilirsiniz.')
      setPrompt('')
    } catch (e) {
      setError('İçerik oluşturulamadı: ' + e.message)
    } finally {
      setGenerating(false)
    }
  }

  const handleApprove = async (id) => {
    setActionLoading(true)
    try {
      const updated = await api.approvePost(id)
      setPosts(prev => prev.map(p => p.id === id ? updated : p))
    } catch (e) {
      setError(e.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async (id) => {
    setActionLoading(true)
    try {
      const updated = await api.rejectPost(id)
      setPosts(prev => prev.map(p => p.id === id ? updated : p))
    } catch (e) {
      setError(e.message)
    } finally {
      setActionLoading(false)
    }
  }

  const pendingPosts = posts.filter(p => p.status === 'pending')
  const otherPosts = posts.filter(p => p.status !== 'pending')

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-sm text-gray-500 mt-0.5">İçerik oluştur, onayla ve yayınla</p>
        </div>
        <button onClick={loadData} className="btn-secondary flex items-center gap-2">
          <RefreshCw size={14} /> Yenile
        </button>
      </div>

      {/* Stats */}
      {analytics && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <StatCard title="Toplam İçerik" value={analytics.total_posts} color="indigo" />
          <StatCard title="Onaylanan" value={analytics.approved_posts} sub={`%${analytics.approval_rate} onay oranı`} color="green" />
          <StatCard title="Yayınlanan" value={analytics.published_posts} color="indigo" />
          <StatCard title="Reddedilen" value={analytics.rejected_posts} color="red" />
        </div>
      )}

      {/* Generate Form */}
      <div className="card p-6 mb-8">
        <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Sparkles size={18} className="text-indigo-500" />
          Yeni İçerik Oluştur (Gemini AI)
        </h3>
        <form onSubmit={handleGenerate} className="flex flex-col gap-3">
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder={`Örnek: "Yarın saat 20:00'de Latin gecemiz var." veya "Deniz manzaralı kahvaltımızı tanıt."`}
            rows={3}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
          />
          <div className="flex items-center gap-3">
            <select
              value={platform}
              onChange={e => setPlatform(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="instagram">Instagram</option>
              <option value="facebook">Facebook</option>
              <option value="tiktok">TikTok</option>
            </select>
            <button
              type="submit"
              disabled={generating || !prompt.trim()}
              className="btn-primary flex items-center gap-2"
            >
              {generating ? (
                <><span className="animate-spin">⚙️</span> Oluşturuluyor...</>
              ) : (
                <><Sparkles size={14} /> İçerik Oluştur</>
              )}
            </button>
          </div>
          {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
          {success && <p className="text-sm text-green-700 bg-green-50 px-3 py-2 rounded-lg">{success}</p>}
        </form>
      </div>

      {/* Pending Posts */}
      {pendingPosts.length > 0 && (
        <div className="mb-8">
          <h3 className="font-semibold text-gray-700 mb-3">
            Onay Bekleyen ({pendingPosts.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pendingPosts.map(post => (
              <PostCard
                key={post.id}
                post={post}
                onApprove={handleApprove}
                onReject={handleReject}
                loading={actionLoading}
              />
            ))}
          </div>
        </div>
      )}

      {/* Recent Posts */}
      {otherPosts.length > 0 && (
        <div>
          <h3 className="font-semibold text-gray-700 mb-3">Son İçerikler</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {otherPosts.map(post => (
              <PostCard
                key={post.id}
                post={post}
                onApprove={handleApprove}
                onReject={handleReject}
                loading={actionLoading}
              />
            ))}
          </div>
        </div>
      )}

      {!loading && posts.length === 0 && (
        <div className="text-center py-20 text-gray-400">
          <p className="text-4xl mb-3">📭</p>
          <p>Henüz içerik yok. Yukarıdan ilk içeriğini oluştur!</p>
        </div>
      )}
    </div>
  )
}
