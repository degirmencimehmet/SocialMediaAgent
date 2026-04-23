import { useState, useEffect } from 'react'
import { Save, AlertCircle } from 'lucide-react'
import { api } from '../api/client'

const TENANT = 'hotel_001'

const FIELD_GROUPS = [
  {
    title: 'İşletme Profili',
    desc: 'Marka sesi ve RAG için kullanılır',
    fields: [
      { key: 'business_name', label: 'İşletme Adı', type: 'text', placeholder: 'Örn: Mavi Koy Butik Otel' },
      { key: 'business_type', label: 'İşletme Türü', type: 'select',
        options: ['boutique_hotel', 'resort', 'tour_agency', 'restaurant', 'other'] },
      { key: 'location', label: 'Konum', type: 'text', placeholder: 'Örn: Bodrum, Türkiye' },
      { key: 'description', label: 'İşletme Açıklaması', type: 'textarea',
        placeholder: 'İşletmenizi ve sunduğunuz hizmetleri kısaca açıklayın...' },
      { key: 'target_audience', label: 'Hedef Kitle', type: 'text',
        placeholder: 'Örn: Yurt içi çiftler, aile tatilcileri' },
      { key: 'tone_preference', label: 'Tercih Edilen Ton', type: 'select',
        options: ['casual', 'professional', 'festive', 'promotional'] },
    ],
  },
]

const TONE_LABELS = {
  casual: 'Samimi / Günlük',
  professional: 'Profesyonel',
  festive: 'Kutlamacı / Coşkulu',
  promotional: 'Tanıtım / Satış Odaklı',
}

const TYPE_LABELS = {
  boutique_hotel: 'Butik Otel',
  resort: 'Resort / Tatil Köyü',
  tour_agency: 'Tur Acentesi',
  restaurant: 'Restoran / Kafe',
  other: 'Diğer',
}

export default function Settings() {
  const [form, setForm] = useState({
    business_name: '',
    business_type: 'boutique_hotel',
    description: '',
    target_audience: '',
    tone_preference: 'casual',
    location: '',
  })
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getBrand(TENANT)
      .then(data => setForm({
        business_name: data.business_name || '',
        business_type: data.business_type || 'boutique_hotel',
        description: data.description || '',
        target_audience: data.target_audience || '',
        tone_preference: data.tone_preference || 'casual',
        location: data.location || '',
      }))
      .catch(() => {})
  }, [])

  const handleSave = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSaved(false)
    try {
      await api.upsertBrand(form, TENANT)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Ayarlar</h2>
        <p className="text-sm text-gray-500 mt-0.5">Marka profili ve sistem konfigürasyonu</p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {FIELD_GROUPS.map(group => (
          <div key={group.title} className="card p-6 space-y-4">
            <div className="border-b border-gray-100 pb-3">
              <h3 className="font-semibold text-gray-800">{group.title}</h3>
              <p className="text-xs text-gray-500 mt-0.5">{group.desc}</p>
            </div>

            {group.fields.map(field => (
              <div key={field.key}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {field.label}
                </label>
                {field.type === 'textarea' ? (
                  <textarea
                    value={form[field.key]}
                    onChange={e => setForm(f => ({ ...f, [field.key]: e.target.value }))}
                    placeholder={field.placeholder}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                  />
                ) : field.type === 'select' ? (
                  <select
                    value={form[field.key]}
                    onChange={e => setForm(f => ({ ...f, [field.key]: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    {field.options.map(opt => (
                      <option key={opt} value={opt}>
                        {TONE_LABELS[opt] || TYPE_LABELS[opt] || opt}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={form[field.key]}
                    onChange={e => setForm(f => ({ ...f, [field.key]: e.target.value }))}
                    placeholder={field.placeholder}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                )}
              </div>
            ))}
          </div>
        ))}

        {/* Telegram info box */}
        <div className="card p-5 bg-blue-50 border-blue-200">
          <h3 className="font-semibold text-blue-800 flex items-center gap-2 mb-2">
            <AlertCircle size={16} /> Telegram Kurulumu
          </h3>
          <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
            <li>Telegram'da <strong>@BotFather</strong>'a git → <code>/newbot</code> komutunu çalıştır</li>
            <li>Aldığın token'ı <code>.env</code> dosyasında <code>TELEGRAM_BOT_TOKEN</code>'a yaz</li>
            <li><strong>@userinfobot</strong>'a mesaj at → dönen ID'yi <code>TELEGRAM_OWNER_CHAT_ID</code>'ye yaz</li>
            <li>Backend'i yeniden başlat — onay butonları otomatik çalışır</li>
          </ol>
        </div>

        {/* Meta API info box */}
        <div className="card p-5 bg-orange-50 border-orange-200">
          <h3 className="font-semibold text-orange-800 flex items-center gap-2 mb-2">
            <AlertCircle size={16} /> Meta Graph API (Instagram Yayını)
          </h3>
          <ol className="text-sm text-orange-700 space-y-1 list-decimal list-inside">
            <li><strong>developers.facebook.com</strong> → Yeni Business App oluştur</li>
            <li>Instagram Graph API ürününü ekle</li>
            <li>Instagram hesabını Facebook Sayfasına bağla</li>
            <li>System User oluştur, uzun ömürlü access token al (60 gün)</li>
            <li><code>META_ACCESS_TOKEN</code> ve <code>INSTAGRAM_ACCOUNT_ID</code>'yi <code>.env</code>'e yaz</li>
          </ol>
        </div>

        {error && (
          <p className="text-sm text-red-600 bg-red-50 px-4 py-3 rounded-lg">{error}</p>
        )}
        {saved && (
          <p className="text-sm text-green-700 bg-green-50 px-4 py-3 rounded-lg">Ayarlar kaydedildi!</p>
        )}

        <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
          <Save size={14} />
          {loading ? 'Kaydediliyor...' : 'Kaydet'}
        </button>
      </form>
    </div>
  )
}
