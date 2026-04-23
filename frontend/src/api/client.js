const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  // Posts
  getPosts: (params = {}) => {
    const q = new URLSearchParams(params).toString()
    return request(`/posts${q ? '?' + q : ''}`)
  },
  getPost: (id) => request(`/posts/${id}`),
  approvePost: (id) => request(`/posts/${id}/approve`, { method: 'POST' }),
  rejectPost: (id) => request(`/posts/${id}/reject`, { method: 'POST' }),
  generatePost: (body) => request('/generate', {
    method: 'POST',
    body: JSON.stringify(body),
  }),

  // Brand
  getBrand: (tenantId) => request(`/brand?tenant_id=${tenantId}`),
  upsertBrand: (body, tenantId) => request(`/brand?tenant_id=${tenantId}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  }),
  ingestPosts: (body) => request('/ingest', {
    method: 'POST',
    body: JSON.stringify(body),
  }),

  // Analytics
  getAnalytics: (tenantId) => request(`/analytics?tenant_id=${tenantId}`),

  // Calendar
  getCalendar: (tenantId, year, month) =>
    request(`/calendar?tenant_id=${tenantId}&year=${year}&month=${month}`),
  getCalendarPdfUrl: (tenantId, year, month) =>
    `${BASE}/calendar/pdf?tenant_id=${tenantId}&year=${year}&month=${month}`,
  getCalendarJsonUrl: (tenantId, year, month) =>
    `${BASE}/calendar/json?tenant_id=${tenantId}&year=${year}&month=${month}`,

  // Trends
  getTrends: () => request('/trends'),
}
