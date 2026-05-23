import { useState, useRef, useEffect } from 'react'
import { submitQuery } from '../api.js'
import ResultView from './ResultView.jsx'
import './ChatPane.css'

const PROTOCOLS = [
  { id: 'council',    icon: '⚖', label: 'Council',    desc: 'All models → peer review → synthesis' },
  { id: 'debate',     icon: '⚔', label: 'Debate',     desc: 'Pro vs con → rebuttals → verdict' },
  { id: 'redteam',    icon: '🔴', label: 'Red Team',   desc: 'Defend → attack → improve' },
  { id: 'consensus',  icon: '🤝', label: 'Consensus',  desc: 'Iterate until agreement' },
  { id: 'specialist', icon: '🎯', label: 'Specialist', desc: 'Route to domain expert' },
  { id: 'tournament', icon: '🏆', label: 'Tournament', desc: 'Bracket elimination' },
]

export default function ChatPane({ session, onResult }) {
  const [query, setQuery]       = useState('')
  const [protocol, setProtocol] = useState('council')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [elapsed, setElapsed]   = useState(0)
  const textareaRef = useRef(null)
  const timerRef    = useRef(null)

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 200) + 'px'
  }, [query])

  // Elapsed timer while loading
  useEffect(() => {
    if (loading) {
      setElapsed(0)
      timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000)
    } else {
      clearInterval(timerRef.current)
    }
    return () => clearInterval(timerRef.current)
  }, [loading])

  const handleSubmit = async () => {
    const q = query.trim()
    if (!q || loading) return
    setError(null)
    setLoading(true)
    try {
      const result = await submitQuery(q, protocol)
      onResult(result)
      setQuery('')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const proto = PROTOCOLS.find(p => p.id === protocol)

  return (
    <div className="chat-pane">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <span className="chat-title">Vipin Council</span>
          <span className="chat-subtitle">Multi-LLM Deliberation</span>
        </div>
        {session && (
          <div className="chat-session-id">
            <span className="label">session</span>
            <code>{session.id?.slice(0, 8)}</code>
          </div>
        )}
      </div>

      {/* Result area */}
      <div className="chat-body">
        {!session && !loading && (
          <div className="chat-empty">
            <div className="empty-icon">⚡</div>
            <div className="empty-title">Vipin Council</div>
            <div className="empty-sub">Ask anything. Choose a protocol. Get a deliberated answer.</div>
            <div className="empty-protocols">
              {PROTOCOLS.map(p => (
                <button
                  key={p.id}
                  className={`proto-chip ${protocol === p.id ? 'proto-chip--active' : ''}`}
                  onClick={() => setProtocol(p.id)}
                >
                  {p.icon} {p.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="chat-loading">
            <div className="loading-spinner" />
            <div className="loading-text">
              <span className="loading-proto">{proto.icon} {proto.label}</span>
              <span className="loading-elapsed">{elapsed}s</span>
            </div>
            <div className="loading-sub">Running deliberation protocol…</div>
          </div>
        )}

        {session && !loading && <ResultView session={session} />}
      </div>

      {/* Error */}
      {error && (
        <div className="chat-error">
          <span>⚠ {error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Input area */}
      <div className="chat-input-area">
        {/* Protocol selector */}
        <div className="proto-selector">
          {PROTOCOLS.map(p => (
            <button
              key={p.id}
              className={`proto-btn ${protocol === p.id ? 'proto-btn--active' : ''}`}
              onClick={() => setProtocol(p.id)}
              title={p.desc}
              disabled={loading}
            >
              <span className="proto-btn-icon">{p.icon}</span>
              <span className="proto-btn-label">{p.label}</span>
            </button>
          ))}
        </div>

        {/* Textarea + send */}
        <div className="input-row">
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            placeholder={`Ask the ${proto.label} council… (Enter to send, Shift+Enter for newline)`}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            rows={1}
          />
          <button
            className="send-btn"
            onClick={handleSubmit}
            disabled={!query.trim() || loading}
            title="Send (Enter)"
          >
            {loading ? <span className="send-spinner" /> : '↑'}
          </button>
        </div>
      </div>
    </div>
  )
}
