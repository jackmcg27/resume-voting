import { useState } from 'react'
import PDFViewer from '../components/PDFViewer'
import StarRating from '../components/StarRating'
import { useSessionWS } from '../hooks/useSessionWS'

function ThumbsInput({ value, onChange, disabled }) {
  return (
    <div className="thumbs-rating">
      <button
        type="button"
        className={value === 1 ? 'selected' : ''}
        onClick={() => !disabled && onChange?.(1)}
        disabled={disabled}
        title="Thumbs up"
      >
        👍
      </button>
      <button
        type="button"
        className={value === 0 ? 'selected' : ''}
        onClick={() => !disabled && onChange?.(0)}
        disabled={disabled}
        title="Thumbs down"
      >
        👎
      </button>
    </div>
  )
}

function NumericInput({ value, onChange, disabled }) {
  return (
    <div className="numeric-rating">
      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => (
        <button
          key={n}
          type="button"
          className={n === value ? 'selected' : ''}
          onClick={() => !disabled && onChange?.(n)}
          disabled={disabled}
          title={`Score ${n}`}
        >
          {n}
        </button>
      ))}
    </div>
  )
}

function VotingInput({ style, value, onChange, disabled }) {
  if (style === 'thumbs') return <ThumbsInput value={value} onChange={onChange} disabled={disabled} />
  if (style === 'numeric') return <NumericInput value={value} onChange={onChange} disabled={disabled} />
  return <StarRating value={value ?? 0} onChange={onChange} disabled={disabled} />
}

function scoreDisplay(score, style) {
  if (style === 'thumbs') return score === 1 ? '👍' : '👎'
  if (style === 'numeric') return `${score} / 10`
  return '★'.repeat(score) + '☆'.repeat(5 - score)
}

function avgDisplay(avg, style) {
  if (avg == null) return null
  if (style === 'thumbs') return `${Math.round(avg * 100)}% thumbs up`
  if (style === 'numeric') return `${avg} / 10`
  return `${avg} / 5`
}

function hintText(style) {
  if (style === 'thumbs') return 'Give a thumbs up or thumbs down'
  if (style === 'numeric') return 'Select a score from 1 to 10'
  return 'Select a score from 1 to 5 stars'
}

export default function Join() {
  const [nameInput, setNameInput] = useState('')
  const [codeInput, setCodeInput] = useState('')
  const [name, setName] = useState(null)
  const [code, setCode] = useState(null)
  const [joinError, setJoinError] = useState('')
  const [joining, setJoining] = useState(false)
  const [myVotes, setMyVotes] = useState({})
  const [submitting, setSubmitting] = useState(false)

  const { session, connected } = useSessionWS(code, name)

  async function handleJoin(e) {
    e.preventDefault()
    const n = nameInput.trim()
    const c = codeInput.trim().toUpperCase()
    if (!n || !c) return
    setJoining(true)
    setJoinError('')
    try {
      const res = await fetch(`/api/sessions/${c}`)
      if (!res.ok) {
        setJoinError('Session not found. Check the code and try again.')
        return
      }
      setName(n)
      setCode(c)
    } catch {
      setJoinError('Could not reach server.')
    } finally {
      setJoining(false)
    }
  }

  async function submitVote(score) {
    if (submitting || !session?.active_resume_id) return
    setSubmitting(true)
    try {
      const res = await fetch(`/api/sessions/${code}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ panelist_name: name, score }),
      })
      if (res.ok) {
        setMyVotes(prev => ({ ...prev, [session.active_resume_id]: score }))
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (!name || !code) {
    return (
      <div className="join-screen">
        <h1>Resume Screening</h1>
        <p>Enter your name and the session code provided by the moderator.</p>
        <form className="join-card" onSubmit={handleJoin}>
          <input
            placeholder="Your name"
            value={nameInput}
            onChange={e => setNameInput(e.target.value)}
            autoFocus
            required
          />
          <input
            placeholder="Session code (e.g. ABC123)"
            value={codeInput}
            onChange={e => setCodeInput(e.target.value.toUpperCase())}
            required
            style={{ fontFamily: 'monospace', letterSpacing: '2px', textTransform: 'uppercase' }}
          />
          {joinError && (
            <p style={{ color: 'var(--red)', fontSize: 13 }}>{joinError}</p>
          )}
          <button
            type="submit"
            className="btn-primary"
            disabled={!nameInput.trim() || !codeInput.trim() || joining}
          >
            {joining ? 'Joining...' : 'Join Session'}
          </button>
        </form>
      </div>
    )
  }

  const resumes = session?.resumes ?? []
  const panelists = session?.panelists ?? []
  const activeResume = resumes.find(r => r.id === session?.active_resume_id) ?? null
  const votingOpen = session?.voting_open ?? false
  const voteCount = activeResume?.vote_count ?? 0
  const totalPanelists = panelists.length
  const myVote = activeResume ? myVotes[activeResume.id] : null
  const hasVoted = myVote != null
  const voters = activeResume?.voters ?? []
  const style = session?.voting_style ?? 'stars'

  return (
    <div className="panelist-layout">
      <header className="panelist-topbar">
        <h1>Resume Screening</h1>
        <span>Session: <strong>{code}</strong></span>
        <span className="name-badge">{name}</span>
        <span
          className={`connection-dot ${connected ? 'ok' : 'off'}`}
          title={connected ? 'Connected' : 'Reconnecting...'}
        />
      </header>

      <div className="panelist-body">
        <div className="panelist-pdf-area">
          {activeResume ? (
            <PDFViewer url={`/uploads/${activeResume.filename}`} />
          ) : (
            <div className="waiting-card">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ opacity: .3 }}>
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <p>Waiting for the moderator to open a resume...</p>
            </div>
          )}
        </div>

        <div className="panelist-sidebar">
          {activeResume ? (
            <>
              <div className="resume-title">
                <div className="label">Current Resume</div>
                <div>{activeResume.candidate_name || activeResume.original_name}</div>
              </div>

              {votingOpen && !activeResume.revealed && (
                hasVoted ? (
                  <div className="voted-card">
                    <h3>Vote Submitted</h3>
                    <div className="your-score">{scoreDisplay(myVote, style)}</div>
                    <div className="waiting">
                      <div style={{ marginBottom: 6 }}>{voteCount} / {totalPanelists} submitted</div>
                      <div className="progress-bar-wrap">
                        <div
                          className="progress-bar-fill"
                          style={{ width: totalPanelists > 0 ? `${(voteCount / totalPanelists) * 100}%` : '0%' }}
                        />
                      </div>
                      <div style={{ marginTop: 8 }}>
                        {voters.filter(v => v !== name).map(v => (
                          <div key={v} style={{ fontSize: 12, color: 'var(--gray-500)' }}>{v} voted</div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="voting-card">
                    <h3>Rate this candidate</h3>
                    <p className="hint">{hintText(style)}</p>
                    <VotingInput
                      style={style}
                      value={myVote}
                      onChange={score => submitVote(score)}
                      disabled={submitting}
                    />
                    <p className="hint" style={{ fontSize: 11 }}>
                      {voteCount} of {totalPanelists} submitted
                    </p>
                  </div>
                )
              )}

              {!votingOpen && !activeResume.revealed && (
                <div style={{ color: 'var(--gray-400)', fontSize: 13, textAlign: 'center' }}>
                  Waiting for moderator to open voting...
                </div>
              )}

              {activeResume.revealed && (
                <div className="results-card">
                  <h3>Results</h3>
                  {activeResume.average != null && (
                    <div className="avg">{avgDisplay(activeResume.average, style)}</div>
                  )}
                  <div className="scores-list">
                    {Object.entries(activeResume.votes).sort().map(([pName, score]) => (
                      <div key={pName} className="score-row">
                        <span>{pName}{pName === name ? ' (you)' : ''}</span>
                        <span className="stars">{scoreDisplay(score, style)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div style={{ color: 'var(--gray-400)', fontSize: 13, textAlign: 'center' }}>
              {resumes.filter(r => r.status === 'reviewed').length > 0
                ? 'All resumes reviewed. Waiting for moderator.'
                : 'The session is ready. Waiting for the first resume.'}
            </div>
          )}

          <div style={{ marginTop: 'auto', paddingTop: 16, borderTop: '1px solid var(--gray-200)' }}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.6px', color: 'var(--gray-400)', marginBottom: 8 }}>
              In this session ({panelists.length})
            </div>
            {panelists.map(p => (
              <div
                key={p}
                style={{
                  fontSize: 12,
                  padding: '2px 0',
                  fontWeight: p === name ? 600 : 400,
                  color: p === name ? 'var(--blue)' : 'var(--gray-700)',
                }}
              >
                {p}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
