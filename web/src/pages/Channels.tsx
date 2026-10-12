import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'

interface Channel {
  id: number
  name: string
  type: string
  is_active: boolean
  config: Record<string, any>
}

interface Feed {
  id: number
  url: string
  name: string
  is_active: boolean
}

export default function Channels() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [feeds, setFeeds] = useState<Feed[]>([])
  const [loading, setLoading] = useState(true)
  const [showChannelForm, setShowChannelForm] = useState(false)
  const [showFeedForm, setShowFeedForm] = useState(false)
  const [chForm, setChForm] = useState({ name: '', type: 'telegram', config: {} })
  const [feedForm, setFeedForm] = useState({ url: '', name: '' })

  const load = async () => {
    try {
      const [ch, fd] = await Promise.all([api.get('/channels/channels'), api.get('/channels/feeds')])
      setChannels(ch.data)
      setFeeds(fd.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const addChannel = async () => {
    await api.post('/channels/channels', chForm)
    setShowChannelForm(false)
    setChForm({ name: '', type: 'telegram', config: {} })
    load()
  }

  const addFeed = async () => {
    await api.post('/channels/feeds', feedForm)
    setShowFeedForm(false)
    setFeedForm({ url: '', name: '' })
    load()
  }

  const remove = async (type: string, id: number) => {
    await api.delete(`/channels/${type}/${id}`)
    load()
  }

  if (loading) return <div style={{ padding: 24 }}>Loading...</div>

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      <Link to="/" style={{ color: 'var(--blue)' }}>← Back to Dashboard</Link>
      <h1 style={{ fontSize: 28, margin: '16px 0 24px' }}>Channels & Feeds</h1>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h2 style={{ color: 'var(--yellow)' }}>Delivery Channels</h2>
        <button className="btn-primary btn-sm" onClick={() => setShowChannelForm(!showChannelForm)}>+ Add Channel</button>
      </div>
      {showChannelForm && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 12, marginBottom: 12 }}>
            <input placeholder="Name" value={chForm.name} onChange={(e) => setChForm({ ...chForm, name: e.target.value })} />
            <select value={chForm.type} onChange={(e) => setChForm({ ...chForm, type: e.target.value })}>
              <option value="telegram">Telegram</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="email">Email</option>
            </select>
            <button className="btn-primary" onClick={addChannel}>Save</button>
          </div>
          <p style={{ color: 'var(--gray)', fontSize: 12 }}>
            Configure channel-specific settings in .env or pass config JSON. See README for per-channel config schema.
          </p>
        </div>
      )}
      <div style={{ display: 'grid', gap: 8, marginBottom: 32 }}>
        {channels.map((ch) => (
          <div key={ch.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 16 }}>
            <div>
              <strong>{ch.name}</strong> <span style={{ color: 'var(--gray)', fontSize: 12 }}>({ch.type})</span>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span className={`badge badge-${ch.is_active ? 'approved' : 'rejected'}`}>{ch.is_active ? 'active' : 'inactive'}</span>
              <button className="btn-danger btn-sm" onClick={() => remove('channels', ch.id)}>Delete</button>
            </div>
          </div>
        ))}
        {channels.length === 0 && <p style={{ color: 'var(--gray)' }}>No channels configured.</p>}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h2 style={{ color: 'var(--yellow)' }}>RSS Feeds</h2>
        <button className="btn-primary btn-sm" onClick={() => setShowFeedForm(!showFeedForm)}>+ Add Feed</button>
      </div>
      {showFeedForm && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr 1fr', gap: 12 }}>
            <input placeholder="https://example.com/feed.xml" value={feedForm.url} onChange={(e) => setFeedForm({ ...feedForm, url: e.target.value })} />
            <input placeholder="Name (optional)" value={feedForm.name} onChange={(e) => setFeedForm({ ...feedForm, name: e.target.value })} />
            <button className="btn-primary" onClick={addFeed}>Save</button>
          </div>
        </div>
      )}
      <div style={{ display: 'grid', gap: 8 }}>
        {feeds.map((f) => (
          <div key={f.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 16 }}>
            <div>
              <strong>{f.name || f.url}</strong>
              <p style={{ color: 'var(--gray)', fontSize: 12 }}>{f.url}</p>
            </div>
            <button className="btn-danger btn-sm" onClick={() => remove('feeds', f.id)}>Delete</button>
          </div>
        ))}
        {feeds.length === 0 && <p style={{ color: 'var(--gray)' }}>No custom feeds. Using defaults from config/feeds.yaml.</p>}
      </div>
    </div>
  )
}
