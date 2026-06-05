function formatScore(score, style) {
  if (style === 'thumbs') return score === 1 ? '👍' : '👎'
  if (style === 'numeric') return score
  return '★'.repeat(score) + '☆'.repeat(5 - score)
}

function formatAvg(avg, style) {
  if (style === 'thumbs') return `${Math.round(avg * 100)}%`
  return avg
}

function avgHeader(style) {
  if (style === 'thumbs') return '% Up'
  if (style === 'numeric') return 'Avg (1–10)'
  return 'Avg (1–5)'
}

export default function Leaderboard({ resumes, sessionCode, votingStyle = 'stars' }) {
  const reviewed = resumes
    .filter(r => r.revealed)
    .map(r => ({ ...r, average: r.average ?? 0 }))
    .sort((a, b) => b.average - a.average)

  if (reviewed.length === 0) return null

  const allPanelists = [...new Set(reviewed.flatMap(r => Object.keys(r.votes || {})))].sort()

  const rankClass = (i) => {
    if (i === 0) return 'gold'
    if (i === 1) return 'silver'
    if (i === 2) return 'bronze'
    return ''
  }

  return (
    <div className="leaderboard">
      <h2>Leaderboard</h2>
      <p className="subtitle">{reviewed.length} candidate{reviewed.length !== 1 ? 's' : ''} reviewed</p>
      <table className="lb-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Candidate</th>
            {allPanelists.map(p => <th key={p}>{p}</th>)}
            <th>{avgHeader(votingStyle)}</th>
          </tr>
        </thead>
        <tbody>
          {reviewed.map((r, i) => (
            <tr key={r.id}>
              <td><span className={`lb-rank ${rankClass(i)}`}>#{i + 1}</span></td>
              <td>{r.candidate_name || r.original_name}</td>
              {allPanelists.map(p => (
                <td key={p}>
                  {r.votes?.[p] != null
                    ? <span className="lb-stars">{formatScore(r.votes[p], votingStyle)}</span>
                    : <span style={{ color: 'var(--gray-300)' }}>-</span>}
                </td>
              ))}
              <td><span className="lb-avg">{formatAvg(r.average, votingStyle)}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="lb-actions">
        <a
          href={`/api/sessions/${sessionCode}/export.csv`}
          download
          style={{ display: 'inline-block', padding: '7px 16px', border: '1px solid var(--gray-300)', borderRadius: '8px', fontSize: '13px', fontWeight: 500, color: 'var(--gray-700)' }}
        >
          Export CSV
        </a>
      </div>
    </div>
  )
}
