import { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar.jsx'
import ChatPane from './components/ChatPane.jsx'
import { listSessions, getSession, healthCheck } from './api.js'
import './App.css'

export default function App() {
  const [sessions, setSessions]       = useState([])
  const [activeSession, setActive]    = useState(null)  // full session object
  const [pendingResult, setPending]   = useState(null)  // result being streamed in
  const [serverOk, setServerOk]       = useState(null)  // null=checking, true, false

  // Health check on mount
  useEffect(() => {
    healthCheck()
      .then(() => setServerOk(true))
      .catch(() => setServerOk(false))
  }, [])

  // Load session list
  const refreshSessions = useCallback(async () => {
    try {
      const list = await listSessions()
      setSessions(list)
    } catch { /* server may be starting */ }
  }, [])

  useEffect(() => { refreshSessions() }, [refreshSessions])

  const openSession = useCallback(async (id) => {
    try {
      const s = await getSession(id)
      setActive(s)
      setPending(null)
    } catch (e) {
      console.error('Failed to load session', e)
    }
  }, [])

  const onNewResult = useCallback((result) => {
    setPending(result)
    setActive(result)
    refreshSessions()
  }, [refreshSessions])

  const onNewChat = useCallback(() => {
    setActive(null)
    setPending(null)
  }, [])

  return (
    <div className="app-shell">
      {serverOk === false && (
        <div className="server-banner">
          ⚠ Backend not reachable — run <code>uvicorn backend.main:app --reload --port 8000</code>
        </div>
      )}
      <Sidebar
        sessions={sessions}
        activeId={activeSession?.id}
        onSelect={openSession}
        onNewChat={onNewChat}
      />
      <main className="main-pane">
        <ChatPane
          session={activeSession}
          onResult={onNewResult}
        />
      </main>
    </div>
  )
}
