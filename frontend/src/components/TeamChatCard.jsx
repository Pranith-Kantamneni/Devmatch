import { useCallback, useEffect, useState } from 'react'
import { MessagesSquare, BarChart3, Plus, X } from 'lucide-react'
import Card from './ui/Card'
import Button from './ui/Button'
import Modal from './ui/Modal'
import Input from './ui/Input'
import ChatBox from './ChatBox'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'

const POLL_MS = 8000
const PAGE_SIZE = 50

const QUICK_REPLIES = [
  'Welcome to the team! Introduce yourself 👋',
  "Let's plan our first build this week",
  'Share your availability for the hackathon',
]

function PollCard({ poll, canClose, onVote, onClose, voting, closing }) {
  const myVotes = poll.my_option_ids?.length ? poll.my_option_ids : (poll.my_option_id ? [poll.my_option_id] : [])
  return (
    <div className="poll-card">
      <div className="poll-question-row">
        <span className="poll-badge">Poll{poll.allow_multiple ? ' · multi' : ''}</span>
        <span className="poll-question">{poll.question}</span>
      </div>
      <div className="poll-meta">
        {poll.total_votes} vote{poll.total_votes === 1 ? '' : 's'} · by {poll.creator_username || 'Someone'}
        {poll.is_closed && <span className="poll-closed">Closed</span>}
        {!poll.is_closed && poll.allow_multiple && <span className="poll-hint">Pick any number</span>}
      </div>
      <div className="poll-options">
        {(poll.options || []).length === 0 && (
          <p className="section-empty">No options on this poll.</p>
        )}
        {(poll.options || []).map((opt) => {
          const pct = poll.total_votes > 0 ? Math.round((opt.votes / poll.total_votes) * 100) : 0
          const mine = myVotes.includes(opt.id)
          const busy = voting === opt.id
          return (
            <button
              key={opt.id}
              type="button"
              className={`poll-option ${mine ? 'mine' : ''}`}
              disabled={poll.is_closed || voting !== false}
              aria-pressed={mine}
              aria-label={`Vote for ${opt.text}${mine ? ' (your vote)' : ''}`}
              onClick={() => onVote(poll.id, opt.id)}
              title={poll.is_closed ? 'Poll closed' : `Vote for ${opt.text}`}
            >
              <span className="poll-option-fill" style={{ width: `${pct}%` }} />
              <span className="poll-option-text">{busy ? 'Saving…' : opt.text}</span>
              <span className="poll-option-pct">{pct}%</span>
            </button>
          )
        })}
      </div>
      {canClose && !poll.is_closed && (
        <button
          type="button"
          className="poll-close"
          disabled={closing}
          onClick={() => onClose(poll.id)}
        >
          {closing ? 'Closing…' : 'Close poll'}
        </button>
      )}
    </div>
  )
}

function CreatePollModal({ open, onClose, onCreated, projectId }) {
  const { toast } = useToast()
  const [question, setQuestion] = useState('')
  const [options, setOptions] = useState(['', ''])
  const [allowMultiple, setAllowMultiple] = useState(false)
  const [saving, setSaving] = useState(false)

  const reset = () => {
    setQuestion('')
    setOptions(['', ''])
    setAllowMultiple(false)
  }

  const submit = async (e) => {
    e.preventDefault()
    const cleaned = options.map((o) => o.trim()).filter(Boolean)
    if (!question.trim()) {
      toast('Give your poll a question', 'error')
      return
    }
    if (cleaned.length < 2) {
      toast('Add at least 2 options', 'error')
      return
    }
    setSaving(true)
    try {
      await api.createPoll(projectId, { question: question.trim(), options: cleaned, allow_multiple: allowMultiple })
      toast('Poll created')
      reset()
      onClose()
      onCreated()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={() => { if (!saving) { reset(); onClose() } }}
      title="New team poll"
      footer={
        <>
          <Button variant="ghost" disabled={saving} onClick={() => { reset(); onClose() }}>Cancel</Button>
          <Button type="submit" form="poll-form" loading={saving}>Create poll</Button>
        </>
      }
    >
      <form id="poll-form" onSubmit={submit} className="modal-form">
        <Input
          label="Question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Which frontend framework?"
          maxLength={280}
        />
        {options.map((opt, i) => (
          <div key={i} className="poll-opt-row">
            <Input
              label={i === 0 ? 'Options' : undefined}
              value={opt}
              onChange={(e) =>
                setOptions((prev) => prev.map((o, idx) => (idx === i ? e.target.value : o)))
              }
              placeholder={`Option ${i + 1}`}
              aria-label={`Poll option ${i + 1}`}
              maxLength={120}
            />
            {options.length > 2 && (
              <button
                type="button"
                className="icon-btn danger"
                aria-label={`Remove option ${i + 1}`}
                onClick={() => setOptions((prev) => prev.filter((_, idx) => idx !== i))}
              >
                <X size={15} />
              </button>
            )}
          </div>
        ))}
        {options.length < 6 && (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => setOptions((prev) => [...prev, ''])}
          >
            <Plus size={14} /> Add option
          </Button>
        )}
        <label className="toggle-row">
          <input type="checkbox" checked={allowMultiple} onChange={(e) => setAllowMultiple(e.target.checked)} />
          <span className="toggle-label">
            <span className="toggle-title">Allow multiple selections</span>
            <span className="toggle-desc">Voters can pick more than one option</span>
          </span>
        </label>
      </form>
    </Modal>
  )
}

/** Members-only group chat with polls tab. Parent gates on 2+ members. */
export default function TeamChatCard({ projectId, currentUsername, currentUserId, isCreator }) {
  const { toast } = useToast()
  const [tab, setTab] = useState('chat')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [polls, setPolls] = useState([])
  const [pollsLoading, setPollsLoading] = useState(false)
  const [voting, setVoting] = useState(false)
  const [closing, setClosing] = useState(false)
  const [pollModal, setPollModal] = useState(false)

  const loadLatest = useCallback(async () => {
    try {
      const data = await api.listTeamMessages(projectId, { limit: PAGE_SIZE })
      setMessages(data)
      setHasMore(data.length >= PAGE_SIZE)
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [projectId, toast])

  const loadPolls = useCallback(async () => {
    setPollsLoading(true)
    try {
      setPolls(await api.listPolls(projectId))
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setPollsLoading(false)
    }
  }, [projectId, toast])

  useEffect(() => {
    loadLatest()
    // Prefetch polls silently so the tab badge is accurate before opening.
    api.listPolls(projectId).then(setPolls).catch(() => {})
    const timer = setInterval(() => {
      if (document.hidden) return
      api
        .listTeamMessages(projectId, { limit: PAGE_SIZE })
        .then((data) => {
          setMessages(data)
          setHasMore(data.length >= PAGE_SIZE)
        })
        .catch(() => {})
    }, POLL_MS)
    return () => clearInterval(timer)
  }, [loadLatest, projectId])

  useEffect(() => {
    if (tab !== 'polls') return
    loadPolls()
    const timer = setInterval(() => {
      if (document.hidden) return
      api.listPolls(projectId).then(setPolls).catch(() => {})
    }, POLL_MS)
    return () => clearInterval(timer)
  }, [tab, loadPolls, projectId])

  const loadOlder = async () => {
    if (messages.length === 0) return
    try {
      const older = await api.listTeamMessages(projectId, {
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
      const sent = await api.postTeamMessage(projectId, { body: text })
      setMessages((prev) => (prev.some((m) => m.id === sent.id) ? prev : [...prev, sent]))
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSending(false)
    }
  }

  const vote = async (pollId, optionId) => {
    setVoting(optionId)
    try {
      const updated = await api.votePoll(projectId, pollId, { option_id: optionId })
      setPolls((prev) => prev.map((p) => (p.id === pollId ? updated : p)))
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setVoting(false)
    }
  }

  const close = async (pollId) => {
    if (closing) return
    setClosing(true)
    try {
      const updated = await api.closePoll(projectId, pollId)
      setPolls((prev) => prev.map((p) => (p.id === pollId ? updated : p)))
      toast('Poll closed')
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setClosing(false)
    }
  }

  return (
    <Card className="section-card">
      <div className="section-header">
        <div className="section-title-wrap">
          <MessagesSquare size={18} className="section-icon" />
          <h3 className="section-title">Team chat</h3>
          <span className="section-count">{messages.length}</span>
        </div>
        {tab === 'polls' && (
          <Button size="sm" variant="secondary" onClick={() => setPollModal(true)}>
            <Plus size={14} /> New poll
          </Button>
        )}
      </div>

      <div className="tabs chat-tabs">
        <button className={`tab ${tab === 'chat' ? 'active' : ''}`} onClick={() => setTab('chat')}>
          <MessagesSquare size={15} /> Chat
        </button>
        <button className={`tab ${tab === 'polls' ? 'active' : ''}`} onClick={() => setTab('polls')}>
          <BarChart3 size={15} /> Polls
          {polls.filter((p) => !p.is_closed).length > 0 && (
            <span className="tab-count">{polls.filter((p) => !p.is_closed).length}</span>
          )}
        </button>
      </div>

      {tab === 'chat' ? (
        <ChatBox
          messages={messages}
          loading={loading}
          currentUsername={currentUsername}
          onSend={send}
          sending={sending}
          onLoadOlder={loadOlder}
          canLoadOlder={hasMore}
          emptyText="No messages yet. Coordinate your first build here!"
          placeholder="Message the team…"
          suggestions={messages.length === 0 ? QUICK_REPLIES : []}
        />
      ) : pollsLoading && polls.length === 0 ? (
        <div className="skeleton" style={{ height: 120 }} />
      ) : polls.length === 0 ? (
        <p className="section-empty">
          No polls yet. Settle stack choices, meeting times, or task splits with a quick vote.
        </p>
      ) : (
        <div className="poll-list">
          {polls.map((poll) => (
            <PollCard
              key={poll.id}
              poll={poll}
              voting={voting}
              closing={closing}
              canClose={isCreator || poll.creator_id === currentUserId}
              onVote={vote}
              onClose={close}
            />
          ))}
        </div>
      )}

      <CreatePollModal
        open={pollModal}
        onClose={() => setPollModal(false)}
        onCreated={loadPolls}
        projectId={projectId}
      />
    </Card>
  )
}
