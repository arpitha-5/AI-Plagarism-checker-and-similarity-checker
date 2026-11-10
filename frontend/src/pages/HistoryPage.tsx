import { useEffect, useState } from 'react'
import { FileSearch, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../components/common/EmptyState'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { errorMessage, getHistory, type Analysis } from '../services/api'

export default function HistoryPage() {
  const [items, setItems] = useState<Analysis[]>([]); const [error, setError] = useState(''); const [loading, setLoading] = useState(true)
  async function load() { setLoading(true); setError(''); try { setItems(await getHistory()) } catch (err) { setError(errorMessage(err)) } finally { setLoading(false) } }
  useEffect(() => { load() }, [])
  return <div><PageHeader eyebrow="Workspace records" title="Analysis history" description="Review analyses created in your account. Results are loaded from the connected backend." actions={<button className="button button-secondary" onClick={load}><RefreshCw size={15} /> Refresh</button>} />{error && <div className="form-error page-error">{error}</div>}<section className="card history-card">{loading ? <div className="loading">Loading history…</div> : items.length === 0 ? <EmptyState icon={<FileSearch />} title="No analyses yet" description="Your completed analyses will appear here after the backend creates them." action={<Link className="button button-primary" to="/checker">Start an analysis</Link>} /> : <div className="history-table"><div className="table-row table-head"><span>Document</span><span>Status</span><span>Similarity</span><span>Date</span><span /></div>{items.map((item) => <div className="table-row" key={item.id}><strong>{item.document_name || 'Text analysis'}</strong><StatusBadge tone={item.status === 'COMPLETED' ? 'success' : 'warning'}>{item.status}</StatusBadge><span>{item.similarity_percentage == null ? '—' : `${item.similarity_percentage}%`}</span><span>{item.created_at ? new Date(item.created_at).toLocaleDateString() : '—'}</span><Link to={`/results/${item.id}`}>Open</Link></div>)}</div>}</section></div>
}
