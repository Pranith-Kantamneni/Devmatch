import { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import Avatar from './ui/Avatar'
import Button from './ui/Button'

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  } catch {
    return ''
  }
}

/**
 * Reusable chat thread: bubbles, load-older, auto-scroll, send box.
 * Fetching/polling is owned by the parent via props.
 */
export default function ChatBox({
  messages,
  loading,
  currentUsername,
  onSend,
  sending,
  onLoadOlder,
  canLoadOlder,
  emptyText = 'No messages yet. Say hello!',
  placeholder = 'Write a message…',
  suggestions = [],
}) {
  const [draft, setDraft] = useState('')
  const scrollRef = useRef(null)
  const stickRef = useRef(true)

  const handleScroll = () => {
    const el = scrollRef.current
    if (!el) return
    stickRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 120
  }

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const last = messages[messages.length - 1]
    if (stickRef.current || (last && last.sender_username === currentUsername)) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages, currentUsername])

  const submit = (e) => {
    e.preventDefault()
    const text = draft.trim()
    if (!text || sending) return
    stickRef.current = true
    setDraft('')
    onSend(text)
  }

  return (
    <div className="chat">
      {canLoadOlder && (
        <button className="chat-load-older" onClick={onLoadOlder}>
          Load older messages
        </button>
      )}
      <div className="chat-scroll" ref={scrollRef} onScroll={handleScroll} role="log" aria-live="polite" aria-label="Chat messages">
        {loading && messages.length === 0 ? (
          <div className="chat-loading">
            <div className="skeleton" style={{ width: '40%', height: 36 }} />
            <div className="skeleton" style={{ width: '55%', height: 36, alignSelf: 'flex-end' }} />
            <div className="skeleton" style={{ width: '45%', height: 36 }} />
          </div>
        ) : messages.length === 0 ? (
          <p className="section-empty">{emptyText}</p>
        ) : (
          messages.map((m) => {
            const mine = m.sender_username === currentUsername
            return (
              <div key={m.id} className={`chat-msg ${mine ? 'mine' : 'theirs'}`}>
                {!mine && <Avatar name={m.sender_username} size={28} />}
                <div className="chat-bubble">
                  {!mine && <span className="chat-sender">{m.sender_username}</span>}
                  <p className="chat-text">{m.body}</p>
                  <span className="chat-time" title={formatTime(m.created_at)}>
                    {formatTime(m.created_at)}
                  </span>
                </div>
              </div>
            )
          })
        )}
      </div>
      <form className="chat-input-row" onSubmit={submit}>
        <input
          className="input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={placeholder}
          aria-label="Chat message"
          maxLength={2000}
        />
        <Button type="submit" size="sm" disabled={!draft.trim() || sending} aria-label="Send message">
          <Send size={15} />
        </Button>
      </form>
      {suggestions.length > 0 && (
        <div className="chat-suggestions">
          {suggestions.map((s) => (
            <button key={s} type="button" className="filter-chip" onClick={() => setDraft(s)}>
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
