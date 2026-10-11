import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  MapPin, Briefcase, GraduationCap, Link2, ArrowLeft,
  Code2, FolderKanban, Sparkles, UserCheck, MessageCircle,
} from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Avatar from '../components/ui/Avatar'
import Button from '../components/ui/Button'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const EXPERIENCE_LEVELS = {
  student: 'Student', junior: 'Junior', mid: 'Mid-level', senior: 'Senior', lead: 'Lead',
}

export default function Profile() {
  const { userId } = useParams()
  const navigate = useNavigate()
  const { toast } = useToast()
  const { user: me } = useAuth()
  const isOwnProfile = me && String(me.id) === String(userId)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [chatStatus, setChatStatus] = useState(null)
  const [chatBusy, setChatBusy] = useState(false)

  useEffect(() => {
    setLoading(true)
    setNotFound(false)
    setLoadError('')
    setProfile(null)
    setChatStatus(null)
    api
      .getPublicProfile(userId)
      .then(setProfile)
      .catch((err) => {
        if (err.status === 404) setNotFound(true)
        else {
          setLoadError(err.message || 'Could not load this profile')
          toast(err.message, 'error')
        }
      })
      .finally(() => setLoading(false))
    if (!(me && String(me.id) === String(userId))) {
      api
        .chatStatus(userId)
        .then(setChatStatus)
        .catch(() => {})
    }
  }, [userId, toast, me])

  const handleMessage = async () => {
    if (!chatStatus || chatStatus.status === 'none' || chatStatus.status === 'rejected') {
      setChatBusy(true)
      try {
        const req = await api.requestChat({ user_id: parseInt(userId, 10) })
        setChatStatus({ status: 'pending_out', request_id: req.id })
        toast('Chat request sent')
      } catch (err) {
        toast(err.message, 'error')
      } finally {
        setChatBusy(false)
      }
      return
    }
    if (chatStatus.status === 'accepted' && chatStatus.conversation_id) {
      navigate(`/messages?conversation=${chatStatus.conversation_id}`)
      return
    }
    if (chatStatus.status === 'pending_in') {
      navigate('/messages')
      return
    }
  }

  const messageLabel =
    !chatStatus || chatStatus.status === 'none'
      ? 'Message'
      : chatStatus.status === 'pending_out'
        ? 'Request sent'
        : chatStatus.status === 'pending_in'
          ? 'Respond in Messages'
          : chatStatus.status === 'accepted'
            ? 'Open chat'
            : 'Request again'
  const messageDisabled =
    chatBusy || !chatStatus || chatStatus.status === 'pending_out'

  if (loading) {
    return (
      <div className="page">
        <div className="skeleton" style={{ width: 120, height: 16, marginBottom: 20 }} />
        <div className="profile-hero-skeleton">
          <div className="skeleton" style={{ width: 80, height: 80, borderRadius: '50%' }} />
          <div style={{ flex: 1 }}>
            <div className="skeleton" style={{ width: 200, height: 24, marginBottom: 10 }} />
            <div className="skeleton" style={{ width: 140, height: 14, marginBottom: 8 }} />
            <div className="skeleton" style={{ width: 240, height: 14 }} />
          </div>
        </div>
      </div>
    )
  }

  if (notFound) {
    return (
      <div className="page">
        <Card>
          <div className="empty-state">
            <h3 className="empty-title">Profile not found</h3>
            <p className="empty-desc">This developer may have removed their profile.</p>
            <div className="empty-action">
              <Link to="/teammates"><Button variant="secondary"><ArrowLeft size={15} /> Back to teammates</Button></Link>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  if (loadError || !profile) {
    return (
      <div className="page">
        <Card>
          <div className="empty-state">
            <h3 className="empty-title">Could not load profile</h3>
            <p className="empty-desc">{loadError || 'Something went wrong.'}</p>
            <div className="empty-action">
              <Button variant="secondary" onClick={() => window.location.reload()}>Retry</Button>
              <Link to="/teammates"><Button variant="ghost"><ArrowLeft size={15} /> Back to teammates</Button></Link>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="page">
      <Link to="/teammates" className="back-link">
        <ArrowLeft size={16} /> Back to teammates
      </Link>

      <Card className="profile-hero">
        <div className="profile-hero-top">
          <Avatar name={profile.full_name || profile.username || `User ${profile.user_id}`} size={80} />
          <div className="profile-hero-info">
            <h1 className="profile-hero-name">{profile.full_name || profile.username || `User ${profile.user_id}`}</h1>
            <p className="profile-hero-username">@{profile.username || `user-${profile.user_id}`}</p>
            <div className="profile-hero-meta">
              {profile.availability && (
                <span className="profile-meta-item available"><UserCheck size={14} /> Open to teams</span>
              )}
              {profile.location && (
                <span className="profile-meta-item"><MapPin size={14} /> {profile.location}</span>
              )}
              {profile.experience_level && (
                <span className="profile-meta-item">
                  <Briefcase size={14} /> {EXPERIENCE_LEVELS[profile.experience_level] || profile.experience_level}
                </span>
              )}
              {profile.education && (
                <span className="profile-meta-item"><GraduationCap size={14} /> {profile.education}</span>
              )}
              {profile.college && (
                <span className="profile-meta-item"><GraduationCap size={14} /> {profile.college}</span>
              )}
              {profile.branch && (
                <span className="profile-meta-item">{profile.branch}</span>
              )}
            </div>
          </div>
        </div>

        {profile.bio && <p className="profile-hero-bio">{profile.bio}</p>}

        <div className="profile-hero-links">
          {isOwnProfile ? (
            <Link to="/dashboard"><Button size="sm" variant="secondary">Edit my profile</Button></Link>
          ) : (
            <Button size="sm" variant="secondary" disabled={messageDisabled} onClick={handleMessage}>
              <MessageCircle size={14} /> {messageLabel}
            </Button>
          )}
          {profile.github_url && (
            <a href={profile.github_url} target="_blank" rel="noreferrer" className="profile-link"><Link2 size={14} /> GitHub</a>
          )}
          {profile.linkedin_url && (
            <a href={profile.linkedin_url} target="_blank" rel="noreferrer" className="profile-link"><Link2 size={14} /> LinkedIn</a>
          )}
          {profile.portfolio_url && (
            <a href={profile.portfolio_url} target="_blank" rel="noreferrer" className="profile-link"><Link2 size={14} /> Portfolio</a>
          )}
        </div>
      </Card>

      <div className="profile-body">
        <Card className="section-card">
          <div className="section-header">
            <div className="section-title-wrap">
              <Code2 size={18} className="section-icon" />
              <h3 className="section-title">Tech stack</h3>
              <span className="section-count">{profile.skills.length}</span>
            </div>
          </div>
          {profile.skills.length === 0 ? (
            <p className="section-empty">No skills listed</p>
          ) : (
            <div className="profile-skills">
              {profile.skills.map((s) => (
                <div key={s.skill_id} className="profile-skill">
                  <span className="profile-skill-name">{s.name}</span>
                  <Badge variant="neutral">{s.category}</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="section-card">
          <div className="section-header">
            <div className="section-title-wrap">
              <FolderKanban size={18} className="section-icon" />
              <h3 className="section-title">Projects</h3>
              <span className="section-count">{profile.projects.length}</span>
            </div>
          </div>
          {profile.projects.length === 0 ? (
            <p className="section-empty">No projects listed</p>
          ) : (
            <div className="profile-projects">
              {profile.projects.map((p) => (
                <div key={p.id} className="profile-project">
                  <div className="profile-project-top">
                    <span className="profile-project-title">{p.title}</span>
                    {p.url && (
                      <a href={p.url} target="_blank" rel="noreferrer" className="profile-link">
                        <Link2 size={14} /> Live
                      </a>
                    )}
                  </div>
                  {p.description && <p className="profile-project-desc">{p.description}</p>}
                  {p.skills.length > 0 && (
                    <div className="project-skills">
                      {p.skills.map((s) => (
                        <Badge key={s.id} variant="accent">{s.name}</Badge>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>

        {profile.collaboration_preferences && (
          <Card className="section-card">
            <div className="section-header">
              <div className="section-title-wrap">
                <Sparkles size={18} className="section-icon" />
                <h3 className="section-title">Looking for in a team</h3>
              </div>
            </div>
            <p className="section-text">{profile.collaboration_preferences}</p>
          </Card>
        )}
      </div>
    </div>
  )
}
