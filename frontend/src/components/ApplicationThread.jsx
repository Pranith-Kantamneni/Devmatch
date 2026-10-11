import { useCallback, useEffect, useState } from 'react'
import { MessageCircle } from 'lucide-react'
import ChatBox from './ChatBox'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'

const POLL_MS = 8000
const PAGE_SIZE = 50

/** Private applicant ↔ creator thread. Polls only while expanded. */
export default function ApplicationThread({ projectId, applicationId, currentUsername }) {
  const { toast } = useToast()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [hasMore, setHasMore] = useState(false)

  const loadLatest = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.listApplicationMessages(projectId, applicationId, {
        limit: PAGE_SIZE,
      })
      setMessages(data)
      setHasMore(data.length >= PAGE_SIZE)
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [projectId, applicationId, toast])

  useEffect(() => {
    if (!open) return
    loadLatest()
    const timer = setInterval(() => {
      if (document.hidden) return
      api
        .listApplicationMessages(projectId, applicationId, { limit: PAGE_SIZE })
        .then((data) => {
          setMessages(data)
          setHasMore(data.length >= PAGE_SIZE)
        })
        .catch(() => {})
    }, POLL_MS)
    return () => clearInterval(timer)
  }, [open, loadLatest, projectId, applicationId])

  const loadOlder = async () => {
    if (messages.length === 0) return
    try {
      const older = await api.listApplicationMessages(projectId, applicationId, {
        limit: PAGE_SIZE,
        before_id: messages[0].id,
      })
      const known = new Set(messages.map((m) => m.id))
      setMessages([...older.filter((m) => !known.has(m.id)), ...messages])
      setHasMore(older.length >= PAGE_SIZE)
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const send = async (text) => {
    setSending(true)
    try {
      const sent = await api.postApplicationMessage(projectId, applicationId, {
        body: text,
      })
      setMessages((prev) => (prev.some((m) => m.id === sent.id) ? prev : [...prev, sent]))
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="app-thread">
      <button
        className="app-thread-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <MessageCircle size={14} />
        {open ? 'Hide chat' : 'Chat'}
        {messages.length > 0 && !open && (
          <span className="tab-count">{messages.length}</span>
        )}
      </button>
      {open && (
        <div className="app-thread-body">
          <ChatBox
            messages={messages}
            loading={loading}
            currentUsername={currentUsername}
            onSend={send}
            sending={sending}
            onLoadOlder={loadOlder}
            canLoadOlder={hasMore}
            emptyText="Ask about the role, timeline, or stack."
            placeholder="Write to them…"
          />
        </div>
      )}
    </div>
  )
}
