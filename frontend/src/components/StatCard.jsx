export default function StatCard({ title, value, sub, color = 'indigo' }) {
  const colors = {
    indigo: 'bg-indigo-50 text-indigo-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    yellow: 'bg-yellow-50 text-yellow-700',
  }
  return (
    <div className="card p-5">
      <p className="text-sm text-gray-500 mb-1">{title}</p>
      <p className={`text-3xl font-bold ${colors[color].split(' ')[1]}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}
