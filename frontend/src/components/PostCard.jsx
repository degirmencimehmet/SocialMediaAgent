import { useState } from 'react'
import { format } from 'date-fns'
import { tr } from 'date-fns/locale'
import { Instagram, Check, X, Clock, Eye } from 'lucide-react'
import PostPreviewModal from './PostPreviewModal'

const STATUS_STYLES = {
  pending:   'badge bg-yellow-100 text-yellow-700',
  approved:  'badge bg-green-100 text-green-700',
  rejected:  'badge bg-red-100 text-red-700',
  published: 'badge bg-blue-100 text-blue-700',
}

const STATUS_LABELS = {
  pending:   'Bekliyor',
  approved:  'Onaylandı',
  rejected:  'Reddedildi',
  published: 'Yayında',
}

export default function PostCard({ post, onApprove, onReject, loading }) {
  const [previewing, setPreviewing] = useState(false)

  return (
    <>
    {previewing && <PostPreviewModal post={post} onClose={() => setPreviewing(false)} />}
    <div className="card p-5 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Instagram size={16} className="text-pink-500" />
          <span className="text-xs font-medium text-gray-500 uppercase">{post.platform}</span>
          <span className="text-xs text-gray-400">·</span>
          <span className="text-xs text-gray-400 italic">{post.tone}</span>
        </div>
        <span className={STATUS_STYLES[post.status] || STATUS_STYLES.pending}>
          {STATUS_LABELS[post.status] || post.status}
        </span>
      </div>

      {/* Caption */}
      <p className="text-sm text-gray-800 leading-relaxed line-clamp-4">{post.caption}</p>

      {/* Hashtags */}
      {post.hashtags?.length > 0 && (
        <p className="text-xs text-indigo-600 line-clamp-2">
          {post.hashtags.slice(0, 8).join(' ')}
        </p>
      )}

      {/* Image suggestion */}
      {post.image_suggestion && (
        <p className="text-xs text-gray-400 italic">
          🖼 {post.image_suggestion}
        </p>
      )}

      {/* Schedule time */}
      {post.post_time && (
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <Clock size={12} />
          {format(new Date(post.post_time), "d MMM yyyy HH:mm", { locale: tr })}
        </div>
      )}

      {/* Prompt */}
      <p className="text-xs text-gray-400 border-t border-gray-100 pt-2">
        İstek: <span className="italic">"{post.prompt}"</span>
      </p>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          onClick={() => setPreviewing(true)}
          className="flex items-center justify-center gap-1.5 px-3 py-2 bg-gray-100 text-gray-600 rounded-lg text-xs font-medium hover:bg-gray-200 transition-colors"
        >
          <Eye size={14} /> Önizle
        </button>
        {post.status === 'pending' && (
          <>
            <button
              onClick={() => onApprove(post.id)}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              <Check size={14} /> Onayla
            </button>
            <button
              onClick={() => onReject(post.id)}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-red-50 text-red-700 border border-red-200 rounded-lg text-xs font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
            >
              <X size={14} /> Reddet
            </button>
          </>
        )}
      </div>
    </div>
    </>
  )
}
