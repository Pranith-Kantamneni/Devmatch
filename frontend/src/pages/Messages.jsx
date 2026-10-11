import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { MessageCircle, Inbox, Check, X } from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Avatar from '../components/ui/Avatar'
import EmptyState from '../components/ui/EmptyState'
import ChatBox from '../components/ChatBox'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const SEEN_KEY = 'devmatch_dm_seen'
const POLL_MS = 8000

function loadSeen() {
  try {
    return JSON.parse(localStorage.getItem(SEEN_KEY) || '{}')
  } catch {
    return {}
  }
}

function MessageThread({ conversation, currentUsername, onRead }) {
  const { toast } = useToast()
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [sending, setSending] = useState(false)
  const [hasMore, setHasMore] = useState(false)

  const loadLatest = useCallback(async () => {
    setLoadError('')
    try {
      const data = await api.listDMMessages(conversation.id, { limit: 50 })
      setMessages(data)
      setHasMore(data.length >= 50)
      onRead(conversation.id, data[data.length - 1]?.id)
    } catch (err) {
      setLoadError(err.message || 'Could not load messages')
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [conversation.id, onRead, toast])

  useEffect(() => {
    setMessages([])
    setLoading(true)
    loadLatest()
    const poll = () => {
      api
        .listDMMessages(conversation.id, { limit: 50 })
        .then((data) => {
          setMessages(data)
          setHasMore(data.length >= 50)
          onRead(conversation.id, data[data.length - 1]?.id)
        })
        .catch(() => {})
    }
    const timer = setInterval(() => {
      if (document.hidden) return
      poll()
    }, POLL_MS)
    const onVisible = () => {
      if (!document.hidden) poll()
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      clearInterval(timer)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [conversation.id, loadLatest, onRead])

  const loadOlder = async () => {
    if (messages.length === 0) return
    try {
      const older = await api.listDMMessages(conversation.id, {
        limit: 50,
        before_id: messages[0].id,
      })
      const known = new Set(messages.map((m) => m.id))
      setMessages([...older.filter((m) => !known.has(m.id)), ...messages])
      setHasMore(older.length >= 50)
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const send = async (text) => {
    setSending(true)
    try {
      const sent = await api.postDMMessage(conversation.id, { body: text })
      setMessages((prev) => (prev.some((m) => m.id === sent.id) ? prev : [...prev, sent]))
      onRead(conversation.id, sent.id)
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      {loadError && messages.length === 0 && !loading && (
        <div className="thread-error">
          <span>{loadError}</span>
          <button className="link-btn" onClick={loadLatest}>Retry</button>
        </div>
      )}
      <ChatBox
        messages={messages}
        loading={loading}
        currentUsername={currentUsername}
        onSend={send}
        sending={sending}
        onLoadOlder={loadOlder}
        canLoadOlder={hasMore}
        placeholder={`Message ${conversation.other_user?.username || 'them'}…`}
      />
    </>
  )
}

export default function Messages() {
  const { user } = useAuth()
  const { toast } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()
  const [overview, setOverview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('chats')
  const [activeId, setActiveId] = useState(() => {
    const q = searchParams.get('conversation')
    return q ? parseInt(q, 10) : null
  })
  const [seen, setSeen] = useState(loadSeen)
  const seenRef = useRef(seen)
  seenRef.current = seen

  const markRead = useCallback((convoId, lastId) => {
    if (!lastId) return
    setSeen((prev) => {
      if ((prev[convoId] || 0) >= lastId) return prev
      const next = { ...prev, [convoId]: lastId }
      try {
        localStorage.setItem(SEEN_KEY, JSON.stringify(next))
      } catch {
        /* ignore */
      }
      return next
    })
  }, [])

  const loadOverview = useCallback(async () => {
    try {
      setOverview(await api.chatOverview())
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    loadOverview()
  }, [loadOverview])

  // Keep selection in sync with back/forward navigation + shared links.
  useEffect(() => {
    const q = searchParams.get('conversation')
    setActiveId(q ? parseInt(q, 10) : null)
  }, [searchParams])

  const conversations = overview?.conversations || []
  const incoming = overview?.incoming_requests || []
  const outgoing = overview?.outgoing_requests || []
  const active = conversations.find((c) => c.id === activeId) || conversations[0] || null

  const selectConversation = (id) => {
    setActiveId(id)
    setSearchParams(id ? { conversation: String(id) } : {})
  }

  const respond = async (convoId, accept) => {
    try {
      if (accept) await api.acceptChat(convoId)
      else await api.rejectChat(convoId)
      toast(accept ? 'Chat request accepted' : 'Chat request declined')
      loadOverview()
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const hasNew = (c) =>
    c.last_message && (seenRef.current[c.id] || 0) < c.last_message.id

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-header-text">
          <h1 className="page-title">Messages</h1>
          <p className="page-subtitle">Chat one-on-one with any developer</p>
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${tab === 'chats' ? 'active' : ''}`} onClick={() => setTab('chats')}>
          <MessageCircle size={15} /> Chats
        </button>
        <button className={`tab ${tab === 'requests' ? 'active' : ''}`} onClick={() => setTab('requests')}>
          <Inbox size={15} /> Requests
          {incoming.length > 0 && <span className="tab-count">{incoming.length}</span>}
        </button>
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: 320 }} />
      ) : tab === 'requests' ? (
        <div className="dm-requests">
          {incoming.length === 0 && outgoing.length === 0 ? (
            <Card>
              <EmptyState
                icon={<Inbox size={32} />}
                title="No chat requests"
                description="Visit any developer's profile and hit Message to start chatting."
                action={<Link to="/teammates"><Button size="sm">Find developers</Button></Link>}
              />
            </Card>
          ) : (
            <>
              {incoming.map((r) => (
                <Card key={r.id} className="section-card">
                  <div className="request-item">
                    <Avatar name={r.other_user.username} size={40} />
                    <div className="request-main">
                      <Link to={`/developers/${r.other_user.user_id}`} className="request-title">
                        {r.other_user.username}
                      </Link>
                      <p className="request-msg">wants to chat with you</p>
                    </div>
                    <div className="request-actions">
                      <Button size="sm" onClick={() => respond(r.id, true)}>
                        <Check size={14} /> Accept
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => respond(r.id, false)}>
                        <X size={14} /> Decline
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
              {outgoing.map((r) => (
                <Card key={r.id} className="section-card">
                  <div className="request-item">
                    <Avatar name={r.other_user.username} size={40} />
                    <div className="request-main">
                      <span className="request-title">{r.other_user.username}</span>
                      <p className="request-msg">request sent — waiting for them to accept</p>
                    </div>
                  </div>
                </Card>
              ))}
            </>
          )}
        </div>
      ) : conversations.length === 0 ? (
        <Card>
          <EmptyState
            icon={<MessageCircle size={32} />}
            title="No chats yet"
            description="Request a chat from any developer's profile. Once they accept, the conversation appears here."
            action={<Link to="/teammates"><Button size="sm">Find developers</Button></Link>}
          />
        </Card>
      ) : (
        <div className="dm-layout">
          <Card className="section-card dm-list">
            <div className="request-list">
              {conversations.map((c) => (
                <button
                  key={c.id}
                  className={`dm-item ${active?.id === c.id ? 'active' : ''}`}
                  onClick={() => selectConversation(c.id)}
                >
                  <Avatar name={c.other_user.username} size={40} />
                  <span className="dm-item-main">
                    <span className="dm-item-name">
                      {c.other_user.username}
                      {hasNew(c) && <span className="dm-dot" aria-label="New messages" />}
                    </span>
                    <span className="dm-item-preview">
                      {c.last_message
                        ? `${c.last_message.sender_username === user?.username ? 'You: ' : ''}${c.last_message.body.slice(0, 48)}`
                        : 'Say hello!'}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          </Card>
          <Card className="section-card dm-thread">
            {active ? (
              <>
                <div className="dm-thread-header">
                  <Avatar name={active.other_user.username} size={32} />
                  <Link to={`/developers/${active.other_user.user_id}`} className="request-title">
                    {active.other_user.username}
                  </Link>
                </div>
                <MessageThread
                  conversation={active}
                  currentUsername={user?.username || ''}
                  onRead={markRead}
                />
              </>
            ) : (
              <p className="section-empty">Select a conversation</p>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
