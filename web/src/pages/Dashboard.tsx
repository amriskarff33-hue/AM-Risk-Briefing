import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api'

interface Brief {
  id: number
  title: string
  status: string
  created_at: string
  duration: number
  video_path_16: string | null
}

export default function Dashboard() {
  const [briefs, setBriefs] = useState<Brief[]>([])
  const [loading, setLoading] = useState(true)
  const nav = useNavigate()

  const load = async () => {
    try {
      const { data } = await api.get('/briefs')
      setBriefs(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const createBrief = async () => {
    const { data } = await api.post('/briefs', { title: `Brief ${new Date().toLocaleDateString()}` })
    nav(`/briefs/${data.id}`)
  }

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 32 }}>AM RISK <span style={{ color: 'var(--yellow)' }}>DASHBOARD</span></h1>
          <p style={{ color: 'var(--gray)' }}>Daily aviation risk briefing — Built by IAM-ASI</p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <Link to="/channels" className="btn-ghost" style={{ display: 'inline-flex', alignItems: 'center' }}>Channels</Link>
          <button className="btn-primary" onClick={createBrief}>+ New Brief</button>
        </div>
      </div>

      {loading ? (
        <p style={{ color: 'var(--gray)' }}>Loading...</p>
      ) : briefs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 60 }}>
          <p style={{ color: 'var(--gray)', fontSize: 18 }}>No briefs yet. Create your first daily briefing.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 16 }}>
          {briefs.map((b) => (
            <Link to={`/briefs/${b.id}`} key={b.id} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 20 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
                    <h3 style={{ fontSize: 18 }}>{b.title || `Brief #${b.id}`}</h3>
                    <span className={`badge badge-${b.status}`}>{b.status.replace('_', ' ')}</span>
                  </div>
                  <p style={{ color: 'var(--gray)', fontSize: 13 }}>
                    {new Date(b.created_at).toLocaleString()} {b.duration > 0 && `• ${Math.round(b.duration)}s video`}
                  </p>
                </div>
                <span style={{ color: 'var(--blue)', fontSize: 20 }}>→</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
