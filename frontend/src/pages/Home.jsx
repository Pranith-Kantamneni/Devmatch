import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Users, Plus, MessageCircle, Pencil, ArrowRight, ArrowUpRight,
  Sparkles, Inbox, Send, Check, Lightbulb, Shuffle, FolderKanban,
} from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Avatar from '../components/ui/Avatar'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const TIPS = [
  { title: 'Prove your stack', text: 'Tag skills on your projects — recommendations weigh proven skills higher than listed ones.' },
  { title: 'Close your gaps', text: 'Open a team page to see exactly which required skills your roster still misses.' },
  { title: 'Vote, don’t argue', text: 'Settle stack and meeting-time debates with a team poll instead of a long thread.' },
  { title: 'Import in seconds', text: 'Upload your resume on your profile page — skills, projects, and tech are extracted for review.' },
  { title: 'Filter the signal', text: 'On any team page, filter suggestions by skill or show only developers with project proof.' },
  { title: 'Chat before you commit', text: 'Every application has a private thread — talk to the creator before joining.' },
  { title: 'Strength matters', text: 'Profiles with a bio, skills, and a project get dramatically better matches.' },
]

function greeting() {
  const h = new Date().getHours()
  if (h < 5) return 'Up late'
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

function today() {
  return new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })
}

function strengthOf(profile) {
  if (!profile) return 0
  const checks = [
    !!(profile.full_name && profile.full_name.trim()),
    !!(profile.bio && profile.bio.trim()),
    !!profile.experience_level,
    (profile.skills || []).length > 0,
    (profile.projects || []).length > 0,
    !!profile.availability,
  ]
  return Math.round((checks.filter(Boolean).length / checks.length) * 100)
}

function StrengthRing({ value }) {
  const r = 26
  const c = 2 * Math.PI * r
  return (
    <span className="strength-ring" role="img" aria-label={`Profile strength ${value} percent`}>
      <svg width="68" height="68" viewBox="0 0 68 68">
        <circle cx="34" cy="34" r={r} fill="none" stroke="var(--border-strong)" strokeWidth="7" />
        <circle
          cx="34" cy="34" r={r} fill="none"
          stroke="var(--accent)" strokeWidth="7" strokeLinecap="round"
          strokeDasharray={`${((value / 100) * c).toFixed(1)} ${c.toFixed(1)}`}
          transform="rotate(-90 34 34)"
          className="strength-ring-fill"
        />
      </svg>
      <span className="strength-ring-value">{value}%</span>
    </span>
  )
}

const QUICK_ACTIONS = [
  { to: '/teammates', icon: <Users size={20} />, title: 'Find teammates', desc: 'Ranked developers who complement you' },
  { to: '/teams/new', icon: <Plus size={20} />, title: 'Create a team', desc: 'Post a hackathon project in a minute' },
  { to: '/messages', icon: <MessageCircle size={20} />, title: 'Messages', desc: 'Chat requests and 1:1 conversations' },
  { to: '/teams', icon: <FolderKanban size={20} />, title: 'My teams', desc: 'Discover, manage, and apply' },
  { to: '/dashboard', icon: <Pencil size={20} />, title: 'Edit profile', desc: 'Polish how others see you' },
]

export default function Home() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [profile, setProfile] = useState(null)
  const [recs, setRecs] = useState(null)
  const [recsFailed, setRecsFailed] = useState(false)
  const [myTeams, setMyTeams] = useState([])
  const [joinedCount, setJoinedCount] = useState(0)
  const [invitations, setInvitations] = useState([])
  const [applications, setApplications] = useState([])
  const [chatRequests, setChatRequests] = useState(0)
  const [chatCount, setChatCount] = useState(0)
  const [tipIndex, setTipIndex] = useState(() => {
    const day = Math.floor(Date.now() / 86400000)
    return day % TIPS.length
  })

  const load = async () => {
    setLoading(true)
    setLoadFailed(false)
    const [p, r, teams, joined, invs, apps, chat] = await Promise.allSettled([
      api.getMyProfile(),
      api.getRecommendations({ limit: 3 }),
      api.listTeamProjects({ limit: 100 }),
      api.listJoinedTeams(),
      api.listMyInvitations(),
      api.listMyApplications(),
      api.chatOverview(),
    ])
    if (p.status === 'fulfilled') setProfile(p.value)
    else setLoadFailed(true)
    if (r.status === 'fulfilled') {
      setRecs(r.value)
      setRecsFailed(false)
    } else {
      setRecsFailed(true)
    }
    if (teams.status === 'fulfilled' && user) {
      setMyTeams(teams.value.filter((t) => t.creator_id === user.id))
    }
    if (joined.status === 'fulfilled') setJoinedCount(joined.value.length)
    if (invs.status === 'fulfilled') setInvitations(invs.value)
    if (apps.status === 'fulfilled') setApplications(apps.value)
    if (chat.status === 'fulfilled') {
      setChatRequests((chat.value.incoming_requests || []).length)
      setChatCount((chat.value.conversations || []).length)
    }
    setLoading(false)
  }

  useEffect(() => {
    load().catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  const name = profile?.full_name?.split(' ')[0] || user?.username || 'builder'
  const strength = useMemo(() => strengthOf(profile), [profile])

  const attention = useMemo(() => {
    const items = []
    for (const inv of invitations.filter((i) => i.status === 'pending').slice(0, 2)) {
      items.push({
        key: `inv-${inv.id}`,
        icon: <Inbox size={16} />,
        text: `Invite to join ${inv.project_title}`,
        to: '/teams?tab=invitations',
        cta: 'Review',
      })
    }
    for (const app of applications.filter((a) => a.status === 'pending').slice(0, 2)) {
      items.push({
        key: `app-${app.id}`,
        icon: <Send size={16} />,
        text: `Application pending — ${app.project_title || `Team #${app.team_project_id}`}`,
        to: '/teams?tab=applications',
        cta: 'View',
      })
    }
    if (chatRequests > 0) {
      items.push({
        key: 'chat-req',
        icon: <MessageCircle size={16} />,
        text: `${chatRequests} chat request${chatRequests === 1 ? '' : 's'} waiting`,
        to: '/messages',
        cta: 'Respond',
      })
    }
    return items.slice(0, 4)
  }, [invitations, applications, chatRequests])

  const topRecs = (recs?.recommendations || []).slice(0, 3)
  const tip = TIPS[tipIndex % TIPS.length]

  if (loading) {
    return (
      <div className="page">
        <div className="skeleton" style={{ height: 148, marginBottom: 20 }} />
        <div className="skeleton" style={{ height: 120, marginBottom: 20 }} />
        <div className="skeleton" style={{ height: 220 }} />
      </div>
    )
  }

  if (loadFailed && !profile) {
    return (
      <div className="page">
        <Card>
          <EmptyState
            icon={<Users size={32} />}
            title="Couldn't load your home"
            description="Check your connection and try again."
            action={<Button size="sm" variant="secondary" onClick={load}>Retry</Button>}
          />
        </Card>
      </div>
    )
  }

  return (
    <div className="page">
      {/* Greeting + strength */}
      <div className="home-hero">
        <div className="home-hero-text">
          <p className="home-date">{today()}</p>
          <h1 className="home-greeting">{greeting()}, {name}</h1>
          <p className="page-subtitle">
            {strength === 100
              ? 'Your profile is match-ready. Go meet your team.'
              : 'Finish your profile to unlock the best matches.'}
          </p>
        </div>
        <Link to="/dashboard" className="home-strength" title="Open my profile">
          <StrengthRing value={strength} />
          <span className="home-strength-label">
            Profile strength <ArrowUpRight size={13} />
          </span>
        </Link>
      </div>

      {/* Quick actions */}
      <div className="home-actions">
        {QUICK_ACTIONS.map((a) => (
          <Link key={a.to + a.title} to={a.to} className="home-action">
            <span className="home-action-icon">{a.icon}</span>
            <span className="home-action-title">{a.title}</span>
            <span className="home-action-desc">{a.desc}</span>
          </Link>
        ))}
      </div>

      <div className="home-grid">
        <div className="home-main">
          {/* Top matches */}
          <Card className="section-card">
            <div className="section-header">
              <div className="section-title-wrap">
                <Sparkles size={18} className="section-icon" />
                <h3 className="section-title">Your top matches</h3>
              </div>
              <Link to="/teammates" className="btn btn-secondary btn-sm">View all <ArrowRight size={14} /></Link>
            </div>
            {recsFailed ? (
              <div>
                <p className="section-empty">
                  Matches couldn't load. Your profile is fine — try again.
                </p>
                <div className="empty-action" style={{ marginTop: 12 }}>
                  <Button size="sm" variant="secondary" onClick={load}>Retry</Button>
                </div>
              </div>
            ) : topRecs.length === 0 ? (
              <div>
                <p className="section-empty">
                  No matches yet — add skills and projects so the engine can rank developers for you.
                </p>
                <div className="empty-action" style={{ marginTop: 12 }}>
                  <Link to="/dashboard" className="btn btn-primary btn-sm">Complete my profile</Link>
                </div>
              </div>
            ) : (
              <div className="home-match-list">
                {topRecs.map((rec) => {
                  const displayName = rec.profile?.full_name || rec.user.username
                  const overlap = (rec.skill_overlap || []).slice(0, 2).join(' · ')
                  return (
                    <Link key={rec.user.id} to={`/developers/${rec.user.id}`} className="home-match">
                      <Avatar name={displayName} size={44} />
                      <span className="home-match-main">
                        <span className="home-match-name">{displayName}</span>
                        <span className="home-match-sub">
                          {overlap || (rec.profile?.bio ? rec.profile.bio.slice(0, 60) : 'Tap to view profile')}
                        </span>
                      </span>
                      <span className="home-match-score">{Math.round(rec.similarity_score * 100)}%</span>
                    </Link>
                  )
                })}
              </div>
            )}
          </Card>

          {/* Needs attention */}
          <Card className="section-card">
            <div className="section-header">
              <div className="section-title-wrap">
                <Inbox size={18} className="section-icon" />
                <h3 className="section-title">Needs attention</h3>
                {attention.length > 0 && <span className="section-count">{attention.length}</span>}
              </div>
            </div>
            {attention.length === 0 ? (
              <p className="section-empty">
                <Check size={14} style={{ display: 'inline', verticalAlign: '-2px' }} /> You’re all caught up. Nothing waiting on you.
              </p>
            ) : (
              <ul className="home-attention-list">
                {attention.map((item) => (
                  <li key={item.key} className="home-attention-item">
                    <span className="home-attention-icon">{item.icon}</span>
                    <span className="home-attention-text">{item.text}</span>
                    <Link to={item.to} className="fit-link">{item.cta}</Link>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        <div className="home-side">
          {/* Stats */}
          <Card className="section-card">
            <div className="home-stats">
              <div className="home-stat">
                <span className="home-stat-value">{(profile?.skills || []).length}</span>
                <span className="home-stat-label">Skills</span>
              </div>
              <div className="home-stat">
                <span className="home-stat-value">{(profile?.projects || []).length}</span>
                <span className="home-stat-label">Projects</span>
              </div>
              <div className="home-stat">
                <span className="home-stat-value">{myTeams.length + joinedCount}</span>
                <span className="home-stat-label">Teams</span>
              </div>
              <div className="home-stat">
                <span className="home-stat-value">{chatCount}</span>
                <span className="home-stat-label">Chats</span>
              </div>
            </div>
          </Card>

          {/* My teams shortcut */}
          {(myTeams.length > 0 || joinedCount > 0) && (
            <Card className="section-card">
              <div className="section-header">
                <div className="section-title-wrap">
                  <Users size={18} className="section-icon" />
                  <h3 className="section-title">My teams</h3>
                </div>
                <Link to="/teams?tab=mine" className="btn btn-ghost btn-sm">All</Link>
              </div>
              <ul className="home-team-list">
                {myTeams.slice(0, 3).map((t) => (
                  <li key={t.id}>
                    <Link to={`/teams/${t.id}`} className="home-team-link">
                      <span className="home-team-name">{t.title}</span>
                      <span className="home-team-meta">{t.member_count}/{t.max_members}</span>
                    </Link>
                  </li>
                ))}
              </ul>
              {joinedCount > 0 && (
                <p className="home-joined-note">
                  +{joinedCount} joined team{joinedCount === 1 ? '' : 's'} ·{' '}
                  <Link to="/teams?tab=mine" className="fit-link">view all</Link>
                </p>
              )}
            </Card>
          )}

          {/* Tip of the day */}
          <Card className="section-card tip-card">
            <div className="section-header">
              <div className="section-title-wrap">
                <Lightbulb size={18} className="section-icon" />
                <h3 className="section-title">{tip.title}</h3>
              </div>
              <button
                className="icon-btn"
                title="Another tip"
                aria-label="Show another tip"
                onClick={() => setTipIndex((i) => i + 1 + Math.floor(Math.random() * (TIPS.length - 1)))}
              >
                <Shuffle size={15} />
              </button>
            </div>
            <p className="section-text">{tip.text}</p>
            <div className="tip-dots" role="group" aria-label="Choose tip">
              {TIPS.map((t, i) => (
                <button
                  key={t.title}
                  className={`tip-dot ${i === tipIndex % TIPS.length ? 'active' : ''}`}
                  aria-label={`Show tip: ${t.title}`}
                  aria-current={i === tipIndex % TIPS.length}
                  onClick={() => setTipIndex(i)}
                />
              ))}
            </div>
          </Card>

          {/* Invite nudge */}
          <Link to="/teams/new" className="side-cta">
            <div className="side-cta-icon"><Plus size={18} /></div>
            <div className="side-cta-text">
              <span className="side-cta-title">Start a team</span>
              <span className="side-cta-sub">Get matched devs in minutes</span>
            </div>
          </Link>
        </div>
      </div>
    </div>
  )
}
