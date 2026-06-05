import { useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import PDFViewer from '../components/PDFViewer'
import Leaderboard from '../components/Leaderboard'
import { useSessionWS } from '../hooks/useSessionWS'

async function api(path, opts = {}) {
  const res = await fetch(path, opts)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export default function Moderator() {
  const [searchParams] = useSearchParams()
  const [sessionCode, setSessionCode] = useState(() => searchParams.get('session'))
  const [sessionName, setSessionName] = useState('')
  const [creating, setCreating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [showLeaderboard, setShowLeaderboard] = useState(false)
  const [localNames, setLocalNames] = useState({})
  const [votingStyle, setVotingStyle] = useState('stars')
  const fileInputRef = useRef()

  const { session, connected } = useSessionWS(sessionCode)

  async function createSession(e) {
    e.preventDefault()
    setCreating(true)
    try {
      const data = await api('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: sessionName.trim(), voting_style: votingStyle }),
      })
      setSessionCode(data.code)
    } finally {
      setCreating(false)
    }
  }

  async function uploadFiles(files) {
    for (const file of files) {
      const form = new FormData()
      form.append('file', file)
      await fetch(`/api/sessions/${sessionCode}/resumes`, { method: 'POST', body: form })
    }
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function post(path) {
    return fetch(`/api/sessions/${sessionCode}${path}`, { method: 'POST' })
  }

  function del(path) {
    return fetch(`/api/sessions/${sessionCode}${path}`, { method: 'DELETE' })
  }

  async function saveCandidateName(resumeId, name) {
    await fetch(`/api/sessions/${sessionCode}/resumes/${resumeId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate_name: name }),
    })
  }

  function getLocalName(resume) {
    return localNames[resume.id] !== undefined ? localNames[resume.id] : resume.candidate_name
  }

  function displayName(resume) {
    return resume.candidate_name || resume.original_name
  }

  function formatAvg(avg, style) {
    if (avg == null) return null
    if (style === 'thumbs') return `${Math.round(avg * 100)}% up`
    return `${avg} avg`
  }

  function copyCode() {
    navigator.clipboard.writeText(sessionCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  if (!sessionCode) {
    return (
      <div className="welcome-screen">
        <h1>Resume Screening</h1>
        <p>Give this session a name so it's easy to identify later.</p>
        <form className="join-card" onSubmit={createSession}>
          <input
            placeholder="Session name (e.g. Backend Engineer - May 2026)"
            value={sessionName}
            onChange={e => setSessionName(e.target.value)}
            autoFocus
            required
          />
          <div className="voting-style-picker">
            <label className="voting-style-label">Voting style</label>
            <div className="voting-style-options">
              {[
                { value: 'stars',   label: '★ 1–5 Stars' },
                { value: 'thumbs',  label: '👍 Thumbs' },
                { value: 'numeric', label: '# 1–10 Score' },
              ].map(opt => (
                <button
                  key={opt.value}
                  type="button"
                  className={`voting-style-btn${votingStyle === opt.value ? ' selected' : ''}`}
                  onClick={() => setVotingStyle(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
          <button type="submit" className="btn-primary" disabled={!sessionName.trim() || creating}>
            {creating ? 'Creating...' : 'Create Session'}
          </button>
        </form>
      </div>
    )
  }

  const resumes = session?.resumes ?? []
  const panelists = session?.panelists ?? []
  const activeResume = resumes.find(r => r.id === session?.active_resume_id) ?? null
  const pending = resumes.filter(r => r.status === 'pending')
  const reviewed = resumes.filter(r => r.status === 'reviewed' && r.id !== activeResume?.id)
  const votingOpen = session?.voting_open ?? false
  const sessionVotingStyle = session?.voting_style ?? 'stars'
  const voteCount = activeResume?.vote_count ?? 0
  const totalPanelists = panelists.length
  const joinUrl = `${window.location.origin}/join`

  return (
    <div className="mod-layout">
      <header className="mod-topbar">
        <h1>{session?.name || 'Resume Screening'}</h1>
        <div className="session-badge">
          <span className="code">{sessionCode}</span>
          <span className="join-hint">{joinUrl}</span>
          <button className="btn-ghost btn-sm" onClick={copyCode}>
            {copied ? 'Copied' : 'Copy Code'}
          </button>
        </div>
        {resumes.filter(r => r.revealed).length > 0 && (
          <button className="btn-ghost btn-sm" onClick={() => setShowLeaderboard(v => !v)}>
            {showLeaderboard ? 'Back to Session' : `Leaderboard (${resumes.filter(r => r.revealed).length})`}
          </button>
        )}
        <span className={`connection-dot ${connected ? 'ok' : 'off'}`} title={connected ? 'Connected' : 'Reconnecting...'} />
      </header>

      <aside className="sidebar">
        <div className="sidebar-section">
          <h3>Panelists ({panelists.length})</h3>
          <ul className="panelist-list">
            {panelists.length === 0
              ? <li className="empty">Nobody joined yet</li>
              : panelists.map(name => <li key={name}>{name}</li>)}
          </ul>
        </div>

        <div className="sidebar-section" style={{ flex: 1 }}>
          <h3>Resume Queue</h3>
          <div className="upload-btn-wrapper">
            <button className="btn-primary" onClick={() => fileInputRef.current?.click()}>
              Upload PDFs
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              multiple
              hidden
              onChange={e => uploadFiles(Array.from(e.target.files))}
            />
          </div>

          <div className="queue-list">
            {activeResume && (
              <>
                <div className="queue-group-label">Active</div>
                <div className="queue-item active">
                  <input
                    className="candidate-name-input"
                    value={getLocalName(activeResume)}
                    onChange={e => setLocalNames(prev => ({ ...prev, [activeResume.id]: e.target.value }))}
                    onBlur={e => {
                      saveCandidateName(activeResume.id, e.target.value)
                      setLocalNames(prev => { const n = { ...prev }; delete n[activeResume.id]; return n })
                    }}
                    onKeyDown={e => e.key === 'Enter' && e.target.blur()}
                    placeholder={activeResume.original_name}
                  />
                  {activeResume.average != null && (
                    <span className="queue-item-avg">{formatAvg(activeResume.average, sessionVotingStyle)}</span>
                  )}
                </div>
              </>
            )}

            {pending.length > 0 && (
              <>
                <div className="queue-group-label">Pending ({pending.length})</div>
                {pending.map(r => (
                  <div key={r.id} className="queue-item pending">
                    <input
                      className="candidate-name-input"
                      value={getLocalName(r)}
                      onChange={e => setLocalNames(prev => ({ ...prev, [r.id]: e.target.value }))}
                      onBlur={e => {
                        saveCandidateName(r.id, e.target.value)
                        setLocalNames(prev => { const n = { ...prev }; delete n[r.id]; return n })
                      }}
                      onKeyDown={e => e.key === 'Enter' && e.target.blur()}
                      placeholder={r.original_name}
                    />
                    <div className="queue-item-actions">
                      <button
                        className="btn-ghost btn-sm"
                        onClick={() => post(`/resumes/${r.id}/activate`)}
                      >
                        Open
                      </button>
                      <button
                        className="btn-ghost btn-sm"
                        style={{ color: 'var(--red)' }}
                        onClick={() => del(`/resumes/${r.id}`)}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </>
            )}

            {reviewed.length > 0 && (
              <>
                <div className="queue-group-label">Reviewed ({reviewed.length})</div>
                {reviewed.map(r => (
                  <div key={r.id} className="queue-item reviewed">
                    <input
                      className="candidate-name-input"
                      value={getLocalName(r)}
                      onChange={e => setLocalNames(prev => ({ ...prev, [r.id]: e.target.value }))}
                      onBlur={e => {
                        saveCandidateName(r.id, e.target.value)
                        setLocalNames(prev => { const n = { ...prev }; delete n[r.id]; return n })
                      }}
                      onKeyDown={e => e.key === 'Enter' && e.target.blur()}
                      placeholder={r.original_name}
                    />
                    <div className="queue-item-actions">
                      {r.average != null && <span className="queue-item-avg">{formatAvg(r.average, sessionVotingStyle)}</span>}
                      <button
                        className="btn-ghost btn-sm"
                        onClick={() => post(`/resumes/${r.id}/activate`)}
                      >
                        Open
                      </button>
                    </div>
                  </div>
                ))}
              </>
            )}

            {resumes.length === 0 && (
              <p style={{ color: 'var(--gray-400)', fontSize: 12, marginTop: 8 }}>
                Upload PDFs to build the queue.
              </p>
            )}
          </div>
        </div>
      </aside>

      <main className="main-content">
        {showLeaderboard ? (
          <div style={{ flex: 1, overflowY: 'auto' }}>
            <Leaderboard resumes={resumes} sessionCode={sessionCode} votingStyle={sessionVotingStyle} />
          </div>
        ) : activeResume ? (
          <>
            <div className="resume-toolbar">
              <input
                className="candidate-name-input-lg"
                value={getLocalName(activeResume)}
                onChange={e => setLocalNames(prev => ({ ...prev, [activeResume.id]: e.target.value }))}
                onBlur={e => {
                  saveCandidateName(activeResume.id, e.target.value)
                  setLocalNames(prev => { const n = { ...prev }; delete n[activeResume.id]; return n })
                }}
                onKeyDown={e => e.key === 'Enter' && e.target.blur()}
                placeholder={activeResume.original_name}
              />

              <div className="controls-row">
                {!votingOpen && !activeResume.revealed && (
                  <button className="btn-primary" onClick={() => post('/voting/open')}>
                    Open Voting
                  </button>
                )}
                {votingOpen && (
                  <>
                    <span className="vote-counter">
                      {voteCount} / {totalPanelists} submitted
                    </span>
                    <button className="btn-ghost" onClick={() => post('/voting/close')}>
                      Close Voting
                    </button>
                    <button className="btn-success" onClick={() => post('/reveal')}>
                      Reveal Results
                    </button>
                  </>
                )}
                {activeResume.revealed && !votingOpen && (
                  <button
                    className="btn-primary"
                    onClick={() => {
                      const next = pending[0]
                      if (next) post(`/resumes/${next.id}/activate`)
                      else post('/deactivate')
                    }}
                  >
                    {pending.length > 0 ? 'Next Resume' : 'View Results'}
                  </button>
                )}
              </div>
            </div>

            {activeResume.revealed && (
              <div className="revealed-bar" style={{ margin: '0 20px 12px' }}>
                <span>Results:</span>
                <div className="score-chips">
                  {Object.entries(activeResume.votes).map(([name, score]) => (
                    <span key={name} className="score-chip">
                      {name}: <span className="stars">{'★'.repeat(score)}</span>
                    </span>
                  ))}
                </div>
                {activeResume.average != null && (
                  <span className="avg">Avg: {formatAvg(activeResume.average, sessionVotingStyle)}</span>
                )}
              </div>
            )}

            {votingOpen && totalPanelists > 0 && (
              <div style={{ padding: '0 20px 12px' }}>
                <div className="progress-bar-wrap">
                  <div
                    className="progress-bar-fill"
                    style={{ width: `${(voteCount / totalPanelists) * 100}%` }}
                  />
                </div>
              </div>
            )}

            <PDFViewer url={`/uploads/${activeResume.filename}`} />
          </>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
            {reviewed.length > 0 ? (
              <div style={{ flex: 1, overflowY: 'auto' }}>
                <Leaderboard resumes={resumes} sessionCode={sessionCode} votingStyle={sessionVotingStyle} />
              </div>
            ) : (
              <div className="empty-main">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                <p>Select a resume from the queue to begin.</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
