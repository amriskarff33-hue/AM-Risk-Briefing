import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api'

interface BriefDetail {
  id: number
  title: string
  script: string
  story: string
  status: string
  provider: string
  video_path_16: string | null
  video_path_9: string | null
  audio_path: string | null
  duration: number
  items: Array<{ title: string; source: string; link: string }>
  deliveries: Array<{ id: number; channel_id: number; status: string; error: string | null }>
}

export default function BriefDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const [brief, setBrief] = useState<BriefDetail | null>(null)
  const [script, setScript] = useState('')
  const [loading, setLoading] = useState(true)
  const [action, setAction] = useState('')

  const load = async () => {
    try {
      const { data } = await api.get(`/briefs/${id}`)
      setBrief(data)
      setScript(data.script || '')
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  const doAction = async (fn: () => Promise<any>, label: string) => {
    setAction(label)
    try {
      await fn()
      await load()
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Action failed')
    } finally {
      setAction('')
    }
  }

  if (loading) return <div style={{ padding: 24 }}>Loading...</div>
  if (!brief) return <div style={{ padding: 24 }}>Brief not found</div>

  const canGenerate = brief.status === 'draft' || brief.status === 'failed'
  const canSubmit = brief.status === 'draft' && script.trim()
  const canApprove = brief.status === 'pending_review'
  const canPublish = brief.status === 'approved' && brief.video_path_16

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <button className="btn-ghost btn-sm" onClick={() => nav('/')} style={{ marginBottom: 16 }}>← Back</button>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 28 }}>{brief.title || `Brief #${brief.id}`}</h1>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 4 }}>
            <span className={`badge badge-${brief.status}`}>{brief.status.replace('_', ' ')}</span>
            <span style={{ color: 'var(--gray)', fontSize: 13 }}>via {brief.provider}</span>
            {brief.duration > 0 && <span style={{ color: 'var(--gray)', fontSize: 13 }}>{Math.round(brief.duration)}s</span>}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {canGenerate && (
            <button className="btn-primary" disabled={!!action}
              onClick={() => doAction(() => api.post(`/briefs/${id}/generate`), 'Generating...')}>
              {action === 'Generating...' ? 'Generating...' : 'Generate Video'}
            </button>
          )}
          {canSubmit && (
            <button className="btn-ghost" disabled={!!action}
              onClick={() => doAction(() => api.patch(`/briefs/${id}`, { script, status: 'pending_review' }), 'Submitting...')}>
              Submit for Review
            </button>
          )}
          {canApprove && (
            <>
              <button className="btn-primary" disabled={!!action}
                onClick={() => doAction(() => api.post(`/briefs/${id}/approve`), 'Approving...')}>
                Approve
              </button>
              <button className="btn-danger" disabled={!!action}
                onClick={() => doAction(() => api.post(`/briefs/${id}/reject`), 'Rejecting...')}>
                Reject
              </button>
            </>
          )}
          {canPublish && (
            <button className="btn-primary" disabled={!!action}
              onClick={() => doAction(() => api.post(`/briefs/${id}/publish`), 'Publishing...')}>
              Publish to Channels
            </button>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <h3 style={{ marginBottom: 12, color: 'var(--yellow)' }}>Script</h3>
            <textarea value={script} onChange={(e) => setScript(e.target.value)} rows={12}
              style={{ fontFamily: 'monospace', fontSize: 13, resize: 'vertical' }} />
          </div>
          <div className="card">
            <h3 style={{ marginBottom: 12, color: 'var(--yellow)' }}>Story</h3>
            <p style={{ whiteSpace: 'pre-wrap', fontSize: 14, color: 'rgba(255,255,255,0.85)' }}>{brief.story}</p>
          </div>
        </div>
        <div>
          {brief.video_path_16 ? (
            <div className="card" style={{ marginBottom: 16 }}>
              <h3 style={{ marginBottom: 12, color: 'var(--yellow)' }}>Video Preview (16:9)</h3>
              <video controls src={`/data${brief.video_path_16}`} style={{ width: '100%', borderRadius: 8 }} />
            </div>
          ) : (
            <div className="card" style={{ marginBottom: 16, textAlign: 'center', padding: 40 }}>
              <p style={{ color: 'var(--gray)' }}>No video yet. Click "Generate Video" to create.</p>
            </div>
          )}
          <div className="card" style={{ marginBottom: 16 }}>
            <h3 style={{ marginBottom: 12, color: 'var(--yellow)' }}>Sources ({brief.items?.length || 0})</h3>
            <div style={{ maxHeight: 200, overflow: 'auto' }}>
              {(brief.items || []).slice(0, 8).map((item, i) => (
                <div key={i} style={{ marginBottom: 8, fontSize: 13 }}>
                  <a href={item.link} target="_blank" rel="noreferrer">{item.title}</a>
                  <span style={{ color: 'var(--gray)' }}> — {item.source}</span>
                </div>
              ))}
            </div>
          </div>
          {brief.deliveries?.length > 0 && (
            <div className="card">
              <h3 style={{ marginBottom: 12, color: 'var(--yellow)' }}>Deliveries</h3>
              {brief.deliveries.map((d) => (
                <div key={d.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                  <span>Channel #{d.channel_id}</span>
                  <span className={`badge badge-${d.status}`}>{d.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
