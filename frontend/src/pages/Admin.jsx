import { useEffect, useState } from 'react'
import Leaderboard from '../components/Leaderboard'

function StatusBadge({ session }) {
  if (session.voting_open) return <span className="badge badge-amber">Voting open</span>
  if (session.reviewed_count === session.resume_count && session.resume_count > 0)
    return <span className="badge badge-green">Complete</span>
  if (session.active_resume_id)
    return <span className="badge badge-blue">In progress</span>
  return <span className="badge badge-gray">Idle</span>
}

function SessionRow({ session }) {
  const [expanded, setExpanded] = useState(false)
  const [resumes, setResumes] = useState(null)
  const [loading, setLoading] = useState(false)

  async function toggleResults() {
    if (expanded) { setExpanded(false); return }
    setExpanded(true)
    setLoading(true)
    try {
      const res = await fetch(`/api/sessions/${session.code}`)
      const data = await res.json()
      setResumes(data.resumes ?? [])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <tr>
        <td>
          {session.name && (
            <div style={{ fontWeight: 600, marginBottom: 2 }}>{session.name}</div>
          )}
          <span style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--gray-400)', letterSpacing: '1px' }}>
            {session.code}
          </span>
        </td>
        <td><StatusBadge session={session} /></td>
        <td>{session.panelist_count}</td>
        <td>{session.resume_count}</td>
        <td>
          {session.reviewed_count} / {session.resume_count}
          {session.resume_count > 0 && (
            <span style={{ color: 'var(--gray-400)', marginLeft: 6, fontSize: 11 }}>
              ({Math.round((session.reviewed_count / session.resume_count) * 100)}%)
            </span>
          )}
        </td>
        <td>
          <div style={{ display: 'flex', gap: 6 }}>
            {session.reviewed_count > 0 && (
              <button className="btn-ghost btn-sm" onClick={toggleResults}>
                {expanded ? 'Hide Results' : 'View Results'}
              </button>
            )}
            {session.reviewed_count > 0 && (
              <a
                href={`/api/sessions/${session.code}/export.csv`}
                download
                style={{ display: 'inline-block', padding: '4px 10px', border: '1px solid var(--gray-300)', borderRadius: '6px', fontSize: '12px', fontWeight: 500, color: 'var(--gray-700)' }}
              >
                Export CSV
              </a>
            )}
          </div>
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={6} style={{ padding: 0, background: 'var(--gray-50)', borderBottom: '2px solid var(--gray-200)' }}>
            {loading && <p style={{ padding: '16px 24px', color: 'var(--gray-400)' }}>Loading...</p>}
            {!loading && resumes !== null && (
              <Leaderboard resumes={resumes} sessionCode={session.code} />
            )}
          </td>
        </tr>
      )}
    </>
  )
}

export default function Admin() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/admin/sessions')
      if (!res.ok) throw new Error('Failed to load sessions')
      setSessions(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="admin-layout">
      <header className="admin-header">
        <h1>Admin - All Sessions</h1>
        <button className="btn-ghost btn-sm" onClick={load}>Refresh</button>
      </header>

      <div className="admin-body">
        {loading && <p className="admin-empty">Loading...</p>}
        {error && <p className="admin-empty" style={{ color: 'var(--red)' }}>{error}</p>}
        {!loading && !error && sessions.length === 0 && (
          <p className="admin-empty">No sessions have been created yet.</p>
        )}

        {!loading && sessions.length > 0 && (
          <table className="lb-table">
            <thead>
              <tr>
                <th>Session</th>
                <th>Status</th>
                <th>Panelists</th>
                <th>Resumes</th>
                <th>Reviewed</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(s => <SessionRow key={s.code} session={s} />)}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
