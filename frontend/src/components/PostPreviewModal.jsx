import { useEffect } from 'react'
import { X, Heart, MessageCircle, Send, Bookmark, MoreHorizontal } from 'lucide-react'
import { format } from 'date-fns'
import { tr } from 'date-fns/locale'

const PLATFORM_COLORS = {
  instagram: 'from-purple-500 via-pink-500 to-orange-400',
  facebook: 'from-blue-600 to-blue-700',
  tiktok: 'from-gray-900 to-gray-800',
}

export default function PostPreviewModal({ post, onClose }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!post) return null

  const hashtags = post.hashtags || []
  const captionText = post.caption || ''
  const gradientClass = PLATFORM_COLORS[post.platform] || PLATFORM_COLORS.instagram

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className="relative z-10 w-full max-w-sm bg-white rounded-2xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-20 p-1.5 bg-white/90 rounded-full shadow hover:bg-gray-100 transition-colors"
        >
          <X size={16} className="text-gray-600" />
        </button>

        {/* Platform header */}
        <div className={`bg-gradient-to-r ${gradientClass} px-4 py-2 flex items-center gap-2`}>
          <span className="text-white text-xs font-semibold uppercase tracking-wider">
            {post.platform} Önizleme
          </span>
        </div>

        {/* Instagram-style post */}
        <div className="bg-white">
          {/* Profile row */}
          <div className="flex items-center justify-between px-3 py-2.5">
            <div className="flex items-center gap-2.5">
              <div className={`w-8 h-8 rounded-full bg-gradient-to-tr ${gradientClass} p-0.5`}>
                <div className="w-full h-full rounded-full bg-white flex items-center justify-center">
                  <span className="text-xs font-bold text-gray-700">H</span>
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-900 leading-none">hotel_001</p>
                {post.post_time && (
                  <p className="text-[10px] text-gray-400 mt-0.5">
                    {format(new Date(post.post_time), "d MMM HH:mm", { locale: tr })}
                  </p>
                )}
              </div>
            </div>
            <MoreHorizontal size={18} className="text-gray-600" />
          </div>

          {/* Image area */}
          <div className="aspect-square bg-gradient-to-br from-gray-100 to-gray-200 relative flex items-center justify-center overflow-hidden">
            {post.image_url ? (
              <img
                src={post.image_url}
                alt={post.image_suggestion || 'Post görseli'}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="text-center px-6">
                <div className="text-4xl mb-3">🖼️</div>
                {post.image_suggestion ? (
                  <p className="text-sm text-gray-500 leading-relaxed italic">
                    "{post.image_suggestion}"
                  </p>
                ) : (
                  <p className="text-sm text-gray-400">Görsel üretiliyor...</p>
                )}
              </div>
            )}
            {/* Tone badge */}
            {post.tone && (
              <span className="absolute top-3 left-3 bg-black/50 text-white text-[10px] px-2 py-0.5 rounded-full">
                {post.tone}
              </span>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-between px-3 py-2">
            <div className="flex items-center gap-3.5">
              <Heart size={22} className="text-gray-700" />
              <MessageCircle size={22} className="text-gray-700" />
              <Send size={22} className="text-gray-700" />
            </div>
            <Bookmark size={22} className="text-gray-700" />
          </div>

          {/* Caption */}
          <div className="px-3 pb-3">
            <p className="text-xs text-gray-900 leading-relaxed">
              <span className="font-semibold">hotel_001</span>{' '}
              {captionText}
            </p>

            {/* Hashtags */}
            {hashtags.length > 0 && (
              <p className="text-xs text-blue-500 mt-1 leading-relaxed">
                {hashtags.join(' ')}
              </p>
            )}

            {/* Comment count placeholder */}
            <p className="text-[10px] text-gray-400 mt-1.5">
              Tüm yorumları gör
            </p>
          </div>
        </div>

        {/* Footer info */}
        <div className="bg-gray-50 border-t border-gray-100 px-4 py-3">
          <p className="text-[11px] text-gray-400 text-center">
            Bu yalnızca bir önizlemedir — Instagram bağlı değil
          </p>
        </div>
      </div>
    </div>
  )
}
