import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './ResultView.css'

const PROTOCOL_META = {
  council:    { icon: '⚖', label: 'Council',    color: '#5b8af5' },
  debate:     { icon: '⚔', label: 'Debate',     color: '#f87171' },
  redteam:    { icon: '🔴', label: 'Red Team',   color: '#fb923c' },
  consensus:  { icon: '🤝', label: 'Consensus',  color: '#4ade80' },
  specialist: { icon: '🎯', label: 'Specialist', color: '#a78bfa' },
  tournament: { icon: '🏆', label: 'Tournament', color: '#fbbf24' },
}

const MODEL_COLORS = [
  '#5b8af5', '#4ade80', '#f87171', '#fbbf24', '#a78bfa', '#22d3ee',
]

function modelColor(modelId, index) {
  return MODEL_COLORS[index % MODEL_COLORS.length]
}

function shortModel(id) {
  if (!id) return '?'
  const parts = id.split('/')
  return parts[parts.length - 1].replace(/-\d+(\.\d+)*$/, '').replace(/-/g, ' ')
}

function ConfidenceBar({ value }) {
  const pct = Math.round((value || 0) * 100)
  const color = pct >= 70 ? '#4ade80' : pct >= 40 ? '#fbbf24' : '#f87171'
  return (
    <div className="conf-bar-wrap">
      <div className="conf-bar-track">
        <div className="conf-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="conf-bar-label" style={{ color }}>{pct}%</span>
    </div>
  )
}

function ModelTab({ models, activeIdx, onSelect }) {
  return (
    <div className="model-tabs">
      {models.map((m, i) => (
        <button
          key={m.id || i}
          className={`model-tab ${i === activeIdx ? 'model-tab--active' : ''}`}
          style={i === activeIdx ? { borderBottomColor: modelColor(m.id, i), color: modelColor(m.id, i) } : {}}
          onClick={() => onSelect(i)}
        >
          <span className="model-dot" style={{ background: modelColor(m.id, i) }} />
          {shortModel(m.id)}
        </button>
      ))}
    </div>
  )
}

function StageCard({ stage, index }) {
  const [activeModel, setActiveModel] = useState(0)
  const responses = stage.responses || {}
  const modelIds = Object.keys(responses)

  return (
    <div className="stage-card">
      <div className="stage-card-header">
        <span className="stage-num">{index + 1}</span>
        <span className="stage-name">{stage.name || `Stage ${index + 1}`}</span>
        {stage.agreement_ratio != null && (
          <span className="stage-agreement">
            Agreement: <strong>{Math.round(stage.agreement_ratio * 100)}%</strong>
          </span>
        )}
      </div>

      {modelIds.length > 0 && (
        <>
          <ModelTab
            models={modelIds.map(id => ({ id }))}
            activeIdx={activeModel}
            onSelect={setActiveModel}
          />
          <div className="stage-response md">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {responses[modelIds[activeModel]] || ''}
            </ReactMarkdown>
          </div>
        </>
      )}

      {/* Debate / redteam may have non-responses fields */}
      {stage.verdict && (
        <div className="stage-verdict">
          <span className="verdict-label">Verdict</span>
          <div className="md"><ReactMarkdown remarkPlugins={[remarkGfm]}>{stage.verdict}</ReactMarkdown></div>
        </div>
      )}
    </div>
  )
}

function AuditTrail({ trail }) {
  const [open, setOpen] = useState(false)
  if (!trail?.length) return null
  return (
    <div className="audit-wrap">
      <button className="audit-toggle" onClick={() => setOpen(o => !o)}>
        {open ? '▾' : '▸'} Audit Trail <span className="audit-count">{trail.length} steps</span>
      </button>
      {open && (
        <div className="audit-list">
          {trail.map((step, i) => (
            <div key={i} className="audit-step">
              <span className="audit-step-num">{i + 1}</span>
              <code className="audit-step-data">{JSON.stringify(step)}</code>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ResultView({ session }) {
  const [showStages, setShowStages] = useState(false)
  if (!session) return null

  const meta = PROTOCOL_META[session.protocol] || PROTOCOL_META.council
  const stages = session.stages || []
  const dissent = session.dissent || []

  return (
    <div className="result-view">
      {/* Query echo */}
      <div className="result-query">
        <span className="result-query-icon">💬</span>
        <span className="result-query-text">{session.query}</span>
      </div>

      {/* Protocol badge + confidence */}
      <div className="result-meta-row">
        <span className="proto-badge" style={{ background: meta.color + '22', color: meta.color, borderColor: meta.color + '55' }}>
          {meta.icon} {meta.label}
        </span>
        <div className="result-confidence">
          <span className="conf-label">Confidence</span>
          <ConfidenceBar value={session.confidence} />
        </div>
      </div>

      {/* Final answer */}
      <div className="result-answer">
        <div className="result-answer-header">
          <span className="answer-icon">✦</span>
          <span className="answer-label">Final Answer</span>
        </div>
        <div className="result-answer-body md">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {session.final_answer || ''}
          </ReactMarkdown>
        </div>
      </div>

      {/* Dissent */}
      {dissent.length > 0 && (
        <div className="result-dissent">
          <div className="dissent-header">⚠ Dissenting Views ({dissent.length})</div>
          {dissent.map((d, i) => (
            <div key={i} className="dissent-item md">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {d.length > 400 ? d.slice(0, 400) + '…' : d}
              </ReactMarkdown>
            </div>
          ))}
        </div>
      )}

      {/* Stages toggle */}
      {stages.length > 0 && (
        <div className="stages-section">
          <button className="stages-toggle" onClick={() => setShowStages(s => !s)}>
            {showStages ? '▾' : '▸'} Deliberation Stages
            <span className="stages-count">{stages.length} stages</span>
          </button>
          {showStages && (
            <div className="stages-list">
              {stages.map((stage, i) => (
                <StageCard key={i} stage={stage} index={i} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Audit trail */}
      <AuditTrail trail={session.audit_trail} />
    </div>
  )
}
