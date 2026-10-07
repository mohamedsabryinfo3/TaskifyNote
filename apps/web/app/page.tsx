'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'

type View = 'Dashboard' | 'Tasks' | 'Notes' | 'Sources' | 'AI Assistant' | 'Settings'
type CaptureMode = 'task' | 'note' | 'url'

type Task = {
  id: string
  title: string
  completed: boolean
  priority: 'High' | 'Medium' | 'Low'
}

type Note = {
  id: string
  title: string
  content: string
  sourceUrl?: string
  createdAt: string
}

type Agent = {
  id: string
  name: string
  description: string
}

const nav: View[] = ['Dashboard', 'Tasks', 'Notes', 'Sources', 'AI Assistant', 'Settings']
const seedTasks: Task[] = [
  { id: '1', title: 'Finish project proposal', completed: false, priority: 'High' },
  { id: '2', title: 'Review saved article', completed: false, priority: 'Medium' },
  { id: '3', title: 'Call Ahmed', completed: true, priority: 'Low' },
]
const seedNotes: Note[] = [
  {
    id: 'n1',
    title: 'TaskifyNote launch checklist',
    content: 'Connect API, verify Neon, finish Android build, and ship the first production release.',
    createdAt: new Date().toISOString(),
  },
]

const apiBase = '/api/v1'
const fallbackAgents: Agent[] = [
  { id: 'general', name: 'General Assistant', description: 'Your all-purpose TaskifyNote assistant.' },
  { id: 'planner', name: 'Daily Planner', description: 'Builds a realistic plan and prioritizes what matters most.' },
  { id: 'task-manager', name: 'Task Manager', description: 'Turns ideas into clear, executable tasks.' },
  { id: 'note-analyst', name: 'Note Analyst', description: 'Finds insights, summaries, and action items in saved notes.' },
  { id: 'focus-coach', name: 'Focus Coach', description: 'Helps you choose one clear next move and avoid overload.' },
]
function makeId(prefix: string) {
  return prefix + Math.random().toString(36).slice(2, 10)
}

export default function Page() {
  const [active, setActive] = useState<View>('Dashboard')
  const [tasks, setTasks] = useState<Task[]>(seedTasks)
  const [notes, setNotes] = useState<Note[]>(seedNotes)
  const [search, setSearch] = useState('')
  const [captureOpen, setCaptureOpen] = useState(false)
  const [captureMode, setCaptureMode] = useState<CaptureMode>('task')
  const [taskTitle, setTaskTitle] = useState('')
  const [noteTitle, setNoteTitle] = useState('')
  const [noteContent, setNoteContent] = useState('')
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null)
  const [url, setUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [chatInput, setChatInput] = useState('')
  const [chat, setChat] = useState<{ role: 'user' | 'assistant'; text: string }[]>([
    { role: 'assistant', text: 'Hi! I can help you plan today, turn ideas into tasks, and work with your saved notes.' },
  ])
  const [darkMode, setDarkMode] = useState(true)
  const [syncing, setSyncing] = useState(true)
  const [aiReady, setAiReady] = useState(false)
  const [agents, setAgents] = useState<Agent[]>(fallbackAgents)
  const [selectedAgent, setSelectedAgent] = useState('general')

  useEffect(() => {
    let cancelled = false

    async function loadWorkspace() {
      setSyncing(true)

      try {
        const [tasksResponse, notesResponse] = await Promise.all([
          fetch(apiBase + '/tasks', { cache: 'no-store' }),
          fetch(apiBase + '/notes', { cache: 'no-store' }),
        ])

        if (!tasksResponse.ok || !notesResponse.ok) throw new Error('Workspace sync failed')

        const apiTasks = await tasksResponse.json()
        const apiNotes = await notesResponse.json()

        if (cancelled) return

        setTasks(
          apiTasks.map((task: {
            id: string
            title: string
            status: string
            priority: number
          }) => ({
            id: task.id,
            title: task.title,
            completed: task.status === 'done',
            priority: task.priority >= 2 ? 'High' : task.priority === 1 ? 'Medium' : 'Low',
          })),
        )

        setNotes(
          apiNotes.map((note: {
            id: string
            title: string
            content: string
            source_url?: string | null
            created_at?: string
          }) => ({
            id: note.id,
            title: note.title || 'Untitled note',
            content: note.content || '',
            sourceUrl: note.source_url || undefined,
            createdAt: note.created_at || new Date().toISOString(),
          })),
        )
      } catch {
        try {
          const storedTasks = localStorage.getItem('taskifynote.tasks')
          const storedNotes = localStorage.getItem('taskifynote.notes')
          if (!cancelled) {
            if (storedTasks) setTasks(JSON.parse(storedTasks))
            if (storedNotes) setNotes(JSON.parse(storedNotes))
            showNotice('API unavailable — showing local cache')
          }
        } catch {
          // Keep current state if local storage is unavailable.
        }
      } finally {
        if (!cancelled) setSyncing(false)
      }
    }

    void loadWorkspace()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function checkAi() {
      try {
        const [healthResponse, agentsResponse] = await Promise.all([
          fetch(apiBase + '/health/ai', { cache: 'no-store' }),
          fetch(apiBase + '/ai/agents', { cache: 'no-store' }),
        ])

        if (healthResponse.ok) {
          const health = await healthResponse.json()
          if (!cancelled) setAiReady(Boolean(health.ai_configured))
        }

        if (agentsResponse.ok) {
          const result = await agentsResponse.json()
          if (!cancelled && Array.isArray(result.agents) && result.agents.length) {
            setAgents(result.agents)
          }
        }
      } catch {
        if (!cancelled) setAiReady(false)
      }
    }

    void checkAi()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem('taskifynote.tasks', JSON.stringify(tasks))
      localStorage.setItem('taskifynote.notes', JSON.stringify(notes))
    } catch {
      // Ignore storage errors.
    }
  }, [tasks, notes])

  const filteredTasks = useMemo(
    () => tasks.filter((task) => task.title.toLowerCase().includes(search.toLowerCase())),
    [tasks, search],
  )
  const filteredNotes = useMemo(
    () =>
      notes.filter(
        (note) =>
          note.title.toLowerCase().includes(search.toLowerCase()) ||
          note.content.toLowerCase().includes(search.toLowerCase()),
      ),
    [notes, search],
  )
  const completedCount = tasks.filter((task) => task.completed).length

  function showNotice(message: string) {
    setNotice(message)
    window.setTimeout(() => setNotice(''), 2600)
  }

  async function toggleTask(id: string) {
    const task = tasks.find((item) => item.id === id)
    if (!task) return

    const nextCompleted = !task.completed

    try {
      const response = await fetch(
        apiBase + '/tasks/' + id + (nextCompleted ? '/complete' : ''),
        nextCompleted
          ? { method: 'POST' }
          : {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ status: 'todo' }),
            },
      )

      if (!response.ok) throw new Error('Task update failed')

      setTasks((current) =>
        current.map((item) => (item.id === id ? { ...item, completed: nextCompleted } : item)),
      )
    } catch {
      setTasks((current) =>
        current.map((item) => (item.id === id ? { ...item, completed: nextCompleted } : item)),
      )
      showNotice('API unavailable — task updated locally')
    }
  }

  async function addTask(event: FormEvent) {
    event.preventDefault()
    const title = taskTitle.trim()
    if (!title) return
    setBusy(true)

    try {
      const response = await fetch(apiBase + '/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, priority: 1 }),
      })
      if (!response.ok) throw new Error('API task creation failed')

      const result = await response.json()
      const createdTask: Task = {
        id: result.id,
        title: result.title,
        completed: result.status === 'done',
        priority: result.priority >= 2 ? 'High' : result.priority === 1 ? 'Medium' : 'Low',
      }

      setTasks((current) => [createdTask, ...current])
      setTaskTitle('')
      setCaptureOpen(false)
      showNotice('Task created')
    } catch {
      const localTask: Task = {
        id: makeId('t_'),
        title,
        completed: false,
        priority: 'Medium',
      }
      setTasks((current) => [localTask, ...current])
      showNotice('API unavailable — task saved locally')
      setTaskTitle('')
      setCaptureOpen(false)
    } finally {
      setBusy(false)
    }
  }

  async function addNote(event: FormEvent) {
    event.preventDefault()
    const title = noteTitle.trim()
    const content = noteContent.trim()
    if (!title && !content) return
    const finalTitle = title || 'Untitled note'
    setBusy(true)

    try {
      const response = await fetch(apiBase + '/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: finalTitle, content }),
      })
      if (!response.ok) throw new Error('API note creation failed')

      const result = await response.json()
      const createdNote: Note = {
        id: result.id,
        title: result.title || finalTitle,
        content: result.content || content,
        sourceUrl: result.source_url || undefined,
        createdAt: result.created_at || new Date().toISOString(),
      }

      setNotes((current) => [createdNote, ...current])
      setNoteTitle('')
      setNoteContent('')
      setCaptureOpen(false)
      showNotice('Note created')
    } catch {
      const localNote: Note = {
        id: makeId('n_'),
        title: finalTitle,
        content,
        createdAt: new Date().toISOString(),
      }
      setNotes((current) => [localNote, ...current])
      showNotice('API unavailable — note saved locally')
      setNoteTitle('')
      setNoteContent('')
      setCaptureOpen(false)
    } finally {
      setBusy(false)
    }
  }

  function editNote(note: Note) {
    setEditingNoteId(note.id)
    setNoteTitle(note.title)
    setNoteContent(note.content)
    setCaptureMode('note')
    setCaptureOpen(true)
  }

  async function saveEditedNote(event: FormEvent) {
    event.preventDefault()
    if (!editingNoteId) return
    const title = noteTitle.trim() || 'Untitled note'
    const content = noteContent.trim()
    setBusy(true)

    try {
      const response = await fetch(apiBase + '/notes/' + editingNoteId, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content }),
      })
      if (!response.ok) throw new Error('API note update failed')

      const result = await response.json()
      setNotes((current) =>
        current.map((note) =>
          note.id === editingNoteId
            ? {
                ...note,
                id: result.id || note.id,
                title: result.title || title,
                content: result.content ?? content,
                sourceUrl: result.source_url || note.sourceUrl,
                createdAt: result.created_at || note.createdAt,
              }
            : note,
        ),
      )
      setEditingNoteId(null)
      setNoteTitle('')
      setNoteContent('')
      setCaptureOpen(false)
      showNotice('Note updated')
    } catch {
      setNotes((current) =>
        current.map((note) => (note.id === editingNoteId ? { ...note, title, content } : note)),
      )
      setEditingNoteId(null)
      setNoteTitle('')
      setNoteContent('')
      setCaptureOpen(false)
      showNotice('API unavailable — note updated locally')
    } finally {
      setBusy(false)
    }
  }

  async function deleteTask(id: string) {
    try {
      const response = await fetch(apiBase + '/tasks/' + id, { method: 'DELETE' })
      if (!response.ok) throw new Error('Task delete failed')
      setTasks((current) => current.filter((item) => item.id !== id))
      showNotice('Task deleted')
    } catch {
      setTasks((current) => current.filter((item) => item.id !== id))
      showNotice('API unavailable — task deleted locally')
    }
  }

  async function deleteNote(id: string) {
    try {
      const response = await fetch(apiBase + '/notes/' + id, { method: 'DELETE' })
      if (!response.ok) throw new Error('Note delete failed')
      setNotes((current) => current.filter((item) => item.id !== id))
      showNotice('Note deleted')
    } catch {
      setNotes((current) => current.filter((item) => item.id !== id))
      showNotice('API unavailable — note deleted locally')
    }
  }

  async function captureUrl(event: FormEvent) {
    event.preventDefault()
    const target = url.trim()
    if (!target) return
    setBusy(true)

    try {
      if (!apiBase) throw new Error('API not configured')
      const response = await fetch(apiBase + '/ingest/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: target, save_as_note: true }),
      })
      if (!response.ok) throw new Error('URL capture failed')
      const result = await response.json()
      setNotes((current) => [
        {
          id: result.note_id || makeId('n_'),
          title: result.title || target,
          content: 'Captured from ' + target,
          sourceUrl: target,
          createdAt: new Date().toISOString(),
        },
        ...current,
      ])
      setUrl('')
      setCaptureOpen(false)
      showNotice('Source captured into Notes')
    } catch {
      showNotice('URL capture needs a connected API')
    } finally {
      setBusy(false)
    }
  }

  async function sendChat(event: FormEvent) {
    event.preventDefault()
    const message = chatInput.trim()
    if (!message) return
    setChatInput('')
    setChat((current) => [...current, { role: 'user', text: message }])
    setBusy(true)

    try {
      if (apiBase) {
        const response = await fetch(apiBase + '/ai/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, agent_id: selectedAgent }),
        })
        const result = await response.json()
        if (!response.ok) {
          throw new Error(result.detail || 'AI request failed')
        }
        setChat((current) => [...current, { role: 'assistant', text: result.message || 'I am ready to help.' }])
      } else {
        const reply =
          message.toLowerCase().includes('today')
            ? `You have ${tasks.filter((task) => !task.completed).length} open tasks. Start with “${tasks.find((task) => !task.completed)?.title || 'a small win'}”.`
            : 'I can work with your tasks and notes once the API is connected. For now, I can still help you plan directly in this workspace.'
        setChat((current) => [...current, { role: 'assistant', text: reply }])
      }
    } catch {
      setChat((current) => [...current, { role: 'assistant', text: 'The AI API is unavailable right now.' }])
    } finally {
      setBusy(false)
    }
  }

  function openCapture(mode: CaptureMode = 'task') {
    setCaptureMode(mode)
    setEditingNoteId(null)
    if (mode === 'note') {
      setNoteTitle('')
      setNoteContent('')
    }
    setCaptureOpen(true)
  }

  return (
    <main className={darkMode ? 'app-shell' : 'app-shell light'}>
      <aside className="sidebar">
        <button className="logo button-reset" onClick={() => setActive('Dashboard')} aria-label="Open dashboard">
          Taskify<span>Note</span>
        </button>

        <div className="nav">
          {nav.map((item) => (
            <button
              className={active === item ? 'nav-item active' : 'nav-item'}
              key={item}
              onClick={() => setActive(item)}
            >
              <span>{item}</span>
              {item === 'Tasks' && <b>{tasks.filter((task) => !task.completed).length}</b>}
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          <span>Personal workspace</span>
          <small>v0.7.8 · {syncing ? 'Syncing…' : 'API connected'}</small>
        </div>
      </aside>

      <section className="main">
        <header className="top">
          <div>
            <div className="eyebrow">PERSONAL WORKSPACE</div>
            <h1>{active}</h1>
            <p>Everything important, organized with AI.</p>
          </div>
          <div className="top-actions">
            <button className="search-button" onClick={() => document.getElementById('global-search')?.focus()}>
              Search
            </button>
            <button className="capture" onClick={() => openCapture('task')}>＋ Capture</button>
          </div>
        </header>

        {notice && <div className="notice">{notice}</div>}

        <div className="search-row">
          <input
            id="global-search"
            className="search-input"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search tasks and notes..."
          />
          {search && <button className="clear-search" onClick={() => setSearch('')}>Clear</button>}
        </div>

        {active === 'Dashboard' && (
          <div className="dashboard">
            <section className="card welcome">
              <div>
                <div className="pill">AI READY</div>
                <h2>Good evening 👋</h2>
                <p>Capture a link, organize a task, or ask your assistant anything.</p>
                <div className="quick-actions">
                  <button onClick={() => openCapture('task')}>New task</button>
                  <button onClick={() => openCapture('note')}>New note</button>
                  <button onClick={() => openCapture('url')}>Capture URL</button>
                </div>
              </div>
              <div className="orb">AI</div>
            </section>

            <section className="card">
              <div className="section-head"><h3>Today</h3><button onClick={() => setActive('Tasks')}>{tasks.length} tasks →</button></div>
              {filteredTasks.slice(0, 5).map((task) => (
                <button className="task task-button" key={task.id} onClick={() => toggleTask(task.id)}>
                  <span className={task.completed ? 'check done' : 'check'}>✓</span>
                  <span className={task.completed ? 'strike' : ''}>{task.title}</span>
                  <span className="task-meta">{task.completed ? 'Done' : task.priority}</span>
                </button>
              ))}
            </section>

            <section className="card">
              <div className="section-head"><h3>Progress</h3><span>{completedCount}/{tasks.length} complete</span></div>
              <div className="progress"><span style={{ width: tasks.length ? (completedCount / tasks.length) * 100 + '%' : '0%' }} /></div>
              <p className="muted">Keep moving. One completed task at a time.</p>
              <button className="action secondary" onClick={() => setActive('Tasks')}>Open task board</button>
            </section>

            <section className="card">
              <div className="section-head"><h3>Smart Capture</h3><span>URL → AI</span></div>
              <button className="urlbox url-button" onClick={() => openCapture('url')}>Paste an article URL to extract a note</button>
              <button className="action" onClick={() => openCapture('url')}>Analyze with AI</button>
            </section>

            <section className="card">
              <div className="section-head"><h3>AI Assistant</h3><button onClick={() => setActive('AI Assistant')}>Open →</button></div>
              <button className="chat-preview chat-button" onClick={() => setActive('AI Assistant')}>“What should I work on today?”</button>
              <p className="muted">Ask about tasks, notes, priorities, or your saved sources.</p>
            </section>
          </div>
        )}

        {active === 'Tasks' && (
          <section className="page-grid">
            <div className="card full">
              <div className="section-head"><h2>Task board</h2><button className="action" onClick={() => openCapture('task')}>＋ New task</button></div>
              <div className="task-list">
                {filteredTasks.map((task) => (
                  <div className="task-card" key={task.id}>
                    <button className={task.completed ? 'check done' : 'check'} onClick={() => toggleTask(task.id)} aria-label="Toggle task">✓</button>
                    <div><strong className={task.completed ? 'strike' : ''}>{task.title}</strong><span>{task.completed ? 'Completed' : task.priority + ' priority'}</span></div>
                    <button className="ghost" onClick={() => void deleteTask(task.id)}>Delete</button>
                  </div>
                ))}
                {!filteredTasks.length && <EmptyState title="No matching tasks" action="Create task" onClick={() => openCapture('task')} />}
              </div>
            </div>
          </section>
        )}

        {active === 'Notes' && (
          <section className="page-grid">
            <div className="card full">
              <div className="section-head"><h2>Your notes</h2><button className="action" onClick={() => openCapture('note')}>＋ New note</button></div>
              <div className="notes-grid">
                {filteredNotes.map((note) => (
                  <article className="note-card" key={note.id}>
                    <div className="note-top">
                      <span className="pill">{note.sourceUrl ? 'SOURCE NOTE' : 'NOTE'}</span>
                      <div className="note-actions">
                        <button className="ghost" onClick={() => editNote(note)}>Edit</button>
                        <button className="ghost danger" onClick={() => void deleteNote(note.id)}>Delete</button>
                      </div>
                    </div>
                    <button className="note-body" onClick={() => editNote(note)} aria-label={'Edit ' + note.title}>
                      <h3>{note.title || 'Untitled note'}</h3>
                      <p>{note.content.trim() ? note.content : 'No content yet. Click Edit to start writing.'}</p>
                    </button>
                    {note.sourceUrl && <a href={note.sourceUrl} target="_blank" rel="noreferrer">{note.sourceUrl}</a>}
                    <div className="note-footer"><span>{new Date(note.createdAt).toLocaleDateString()}</span><button className="text-button" onClick={() => editNote(note)}>Open note →</button></div>
                  </article>
                ))}
                {!filteredNotes.length && <EmptyState title="No notes yet" action="Create note" onClick={() => openCapture('note')} />}
              </div>
            </div>
          </section>
        )}

        {active === 'Sources' && (
          <section className="page-grid">
            <div className="card full">
              <div className="section-head"><h2>Saved sources</h2><button className="action" onClick={() => openCapture('url')}>＋ Capture URL</button></div>
              <div className="source-list">
                {notes.filter((note) => note.sourceUrl).map((note) => (
                  <a className="source-item" href={note.sourceUrl} target="_blank" rel="noreferrer" key={note.id}>
                    <span className="source-icon">↗</span><div><strong>{note.title}</strong><span>{note.sourceUrl}</span></div><span>Open</span>
                  </a>
                ))}
                {!notes.some((note) => note.sourceUrl) && <EmptyState title="No sources captured" action="Capture a URL" onClick={() => openCapture('url')} />}
              </div>
            </div>
          </section>
        )}

        {active === 'AI Assistant' && (
          <section className="ai-layout">
            <div className="card chat-card">
              <div className="chat-header">
                <div><span className="pill">PRIVATE AI</span><h2>Assistant</h2></div>
                <div className="chat-header-actions">
                  <select
                    className="agent-select"
                    value={selectedAgent}
                    onChange={(event) => setSelectedAgent(event.target.value)}
                    aria-label="Choose AI agent"
                  >
                    {agents.map((agent) => <option value={agent.id} key={agent.id}>{agent.name}</option>)}
                  </select>
                  <span className={aiReady ? 'status ok' : 'status'}>{aiReady ? 'AI ready' : 'AI setup needed'}</span>
                </div>
              </div>
              <p className="agent-description">
                {agents.find((agent) => agent.id === selectedAgent)?.description}
              </p>
              <div className="messages">
                {chat.map((entry, index) => <div className={entry.role === 'user' ? 'message user' : 'message'} key={index}>{entry.text}</div>)}
                {busy && <div className="message">Thinking…</div>}
              </div>
              <form className="chat-form" onSubmit={sendChat}>
                <input value={chatInput} onChange={(event) => setChatInput(event.target.value)} placeholder="Ask anything about your workspace..." />
                <button className="action" disabled={busy}>Send</button>
              </form>
            </div>
            <div className="card assistant-side">
              <h3>Try these</h3>
              {['What should I work on today?', 'Turn my notes into tasks', 'Summarize my saved sources'].map((prompt) => (
                <button key={prompt} onClick={() => setChatInput(prompt)}>{prompt}</button>
              ))}
            </div>
          </section>
        )}

        {active === 'Settings' && (
          <section className="page-grid">
            <div className="card settings-card">
              <div className="setting-row"><div><strong>Dark mode</strong><span>Keep the workspace comfortable at night.</span></div><button className={darkMode ? 'toggle on' : 'toggle'} onClick={() => setDarkMode((value) => !value)}><span /></button></div>
              <div className="setting-row"><div><strong>Data mode</strong><span>{apiBase ? 'Connected API + local cache' : 'Local browser storage'}</span></div><span className="setting-value">{apiBase ? 'Connected' : 'Local'}</span></div>
              <div className="setting-row"><div><strong>Workspace</strong><span>Single-user personal workspace</span></div><span className="setting-value">Personal</span></div>
            </div>
          </section>
        )}
      </section>

      {captureOpen && (
        <div className="modal-backdrop" onMouseDown={() => !busy && setCaptureOpen(false)}>
          <div className="modal" onMouseDown={(event) => event.stopPropagation()}>
            <div className="modal-head"><div><span className="pill">CAPTURE</span><h2>{captureMode === 'task' ? 'New task' : captureMode === 'note' ? (editingNoteId ? 'Edit note' : 'New note') : 'Capture a URL'}</h2></div><button className="close" onClick={() => { setEditingNoteId(null); setCaptureOpen(false) }}>×</button></div>
            <div className="mode-tabs">
              {(['task', 'note', 'url'] as CaptureMode[]).map((mode) => <button className={captureMode === mode ? 'selected' : ''} key={mode} onClick={() => setCaptureMode(mode)}>{mode === 'task' ? 'Task' : mode === 'note' ? 'Note' : 'URL'}</button>)}
            </div>
            {captureMode === 'task' && <form onSubmit={addTask}><input autoFocus value={taskTitle} onChange={(event) => setTaskTitle(event.target.value)} placeholder="What needs to be done?" /><div className="modal-actions"><button type="button" className="ghost" onClick={() => setCaptureOpen(false)}>Cancel</button><button className="action" disabled={busy}>Create task</button></div></form>}
            {captureMode === 'note' && (
              <form onSubmit={editingNoteId ? saveEditedNote : addNote}>
                <input autoFocus value={noteTitle} onChange={(event) => setNoteTitle(event.target.value)} placeholder="Note title" />
                <textarea value={noteContent} onChange={(event) => setNoteContent(event.target.value)} placeholder="Write your note..." rows={10} />
                <div className="note-editor-hint">Use a clear title and keep the important details in the main note body.</div>
                <div className="modal-actions">
                  <button type="button" className="ghost" onClick={() => { setEditingNoteId(null); setCaptureOpen(false) }}>Cancel</button>
                  <button className="action" disabled={busy}>{editingNoteId ? 'Save changes' : 'Save note'}</button>
                </div>
              </form>
            )}
            {captureMode === 'url' && <form onSubmit={captureUrl}><input autoFocus value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com/article" type="url" /><p className="muted">The API will extract the page title and readable content and save it as a note.</p><div className="modal-actions"><button type="button" className="ghost" onClick={() => setCaptureOpen(false)}>Cancel</button><button className="action" disabled={busy}>Capture source</button></div></form>}
          </div>
        </div>
      )}
    </main>
  )
}

function EmptyState({ title, action, onClick }: { title: string; action: string; onClick: () => void }) {
  return <div className="empty"><span>{title}</span><button className="action secondary" onClick={onClick}>{action}</button></div>
}
