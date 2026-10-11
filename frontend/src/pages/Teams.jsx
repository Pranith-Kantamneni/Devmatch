import { useState, useEffect, useCallback, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  Plus, Users, Inbox, Send, Search, MapPin, CheckCircle2, XCircle,
} from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Input from '../components/ui/Input'
import EmptyState from '../components/ui/EmptyState'
import Avatar from '../components/ui/Avatar'
import CollegeSelect from '../components/CollegeSelect'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

function statusBadge(status) {
  if (status === 'accepted') return <Badge variant="success">Accepted</Badge>
  if (status === 'rejected') return <Badge variant="neutral">Rejected</Badge>
  return <Badge variant="accent">Pending</Badge>
}

function TeamCard({ project }) {
  const spotsLeft = project.max_members - project.member_count
  return (
    <Link to={`/teams/${project.id}`} className="dev-card">
      <div className="dev-card-top">
        <div className="team-card-avatar">
          <Users size={22} />
        </div>
        <div className="dev-card-id">
          <h3 className="dev-card-name">{project.title}</h3>
          <p className="dev-card-username">
            {project.member_count}/{project.max_members} members
            {spotsLeft <= 0 && ' · Full'}
          </p>
        </div>
      </div>

      {project.description && <p className="dev-card-bio">{project.description}</p>}

      <div className="dev-card-meta">
        {project.college && (
          <span className="dev-card-meta-item"><MapPin size={13} /> {project.college}</span>
        )}
        {project.require_same_college && (
          <span className="dev-card-meta-item">Same college only</span>
        )}
      </div>

      {project.required_skills.length > 0 && (
        <div className="dev-card-skills">
          {project.required_skills.slice(0, 5).map((s) => (
            <Badge key={s.id} variant="accent">{s.name}</Badge>
          ))}
          {project.required_skills.length > 5 && (
            <Badge variant="neutral">+{project.required_skills.length - 5}</Badge>
          )}
        </div>
      )}

      {project.tech_stack.length > 0 && (
        <div className="dev-card-skills">
          {project.tech_stack.slice(0, 4).map((t) => (
            <Badge key={t} variant="neutral">{t}</Badge>
          ))}
        </div>
      )}

      <div className="dev-card-cta">
        View team
      </div>
    </Link>
  )
}

export default function Teams() {
  const { user } = useAuth()
  const { toast } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()
  const validTabs = ['discover', 'mine', 'applications', 'invitations']
  const [tab, setTab] = useState(() => {
    const q = searchParams.get('tab')
    return validTabs.includes(q) ? q : 'discover'
  })
  const [projects, setProjects] = useState([])
  const [applications, setApplications] = useState([])
  const [invitations, setInvitations] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [collegeFilter, setCollegeFilter] = useState('')
  const [appliedFilters, setAppliedFilters] = useState({ q: '', college: '' })
  const [visibleLimit, setVisibleLimit] = useState(20)
  const [respondingId, setRespondingId] = useState(null)
  const searchTimer = useRef(null)

  // Debounce keystrokes into applied filters so we don't spam the API.
  useEffect(() => {
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => {
      setAppliedFilters({ q: search.trim(), college: collegeFilter.trim() })
      setVisibleLimit(20)
    }, 400)
    return () => clearTimeout(searchTimer.current)
  }, [search, collegeFilter])

  const loadDiscover = useCallback(async () => {
    setLoading(true)
    try {
      const params = { limit: visibleLimit }
      if (appliedFilters.q) params.q = appliedFilters.q
      if (appliedFilters.college) params.college = appliedFilters.college
      setProjects(await api.listTeamProjects(params))
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [toast, appliedFilters, visibleLimit])

  const loadMine = useCallback(async () => {
    if (!user?.id) return
    setLoading(true)
    try {
      const all = await api.listTeamProjects({ limit: 100 })
      setProjects(all.filter((p) => p.creator_id === user.id))
      const apps = await api.listMyApplications()
      setApplications(apps)
      const invs = await api.listMyInvitations()
      setInvitations(invs)
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [toast, user?.id])

  // Keep tab badges fresh even before visiting those tabs.
  useEffect(() => {
    api.listMyApplications().then(setApplications).catch(() => {})
    api.listMyInvitations().then(setInvitations).catch(() => {})
  }, [])

  useEffect(() => {
    if (tab === 'discover') loadDiscover()
    else loadMine()
  }, [tab, loadDiscover, loadMine])

  const switchTab = (next) => {
    setTab(next)
    setSearchParams(next === 'discover' ? {} : { tab: next }, { replace: true })
  }

  const handleRespondInvitation = async (invId, accept) => {
    if (respondingId) return
    setRespondingId(invId)
    try {
      if (accept) await api.acceptInvitation(invId)
      else await api.rejectInvitation(invId)
      toast(accept ? 'Invitation accepted — welcome to the team' : 'Invitation rejected')
      const invs = await api.listMyInvitations()
      setInvitations(invs)
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setRespondingId(null)
    }
  }

  const myTeams = projects.filter((p) => p.creator_id === user?.id)

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-header-text">
          <h1 className="page-title">Teams</h1>
          <p className="page-subtitle">Discover hackathons, form teams, and manage yours</p>
        </div>
        <Link to="/teams/new"><Button><Plus size={15} /> Create team</Button></Link>
      </div>

      <div className="tabs">
        <button className={`tab ${tab === 'discover' ? 'active' : ''}`} onClick={() => switchTab('discover')}>
          <Search size={15} /> Discover
        </button>
        <button className={`tab ${tab === 'mine' ? 'active' : ''}`} onClick={() => switchTab('mine')}>
          <Users size={15} /> My teams
        </button>
        <button className={`tab ${tab === 'applications' ? 'active' : ''}`} onClick={() => switchTab('applications')}>
          <Send size={15} /> Applications
          {applications.filter((a) => a.status === 'pending').length > 0 && (
            <span className="tab-count">{applications.filter((a) => a.status === 'pending').length}</span>
          )}
        </button>
        <button className={`tab ${tab === 'invitations' ? 'active' : ''}`} onClick={() => switchTab('invitations')}>
          <Inbox size={15} /> Invitations
          {invitations.filter((i) => i.status === 'pending').length > 0 && (
            <span className="tab-count">{invitations.filter((i) => i.status === 'pending').length}</span>
          )}
        </button>
      </div>

      {tab === 'discover' && (
        <form
          className="teams-filters"
          onSubmit={(e) => {
            e.preventDefault()
            setAppliedFilters({ q: search.trim(), college: collegeFilter.trim() })
          }}
        >
          <Input label="Search teams" placeholder="Search teams..." value={search} onChange={(e) => setSearch(e.target.value)} />
          <CollegeSelect
            label="College"
            placeholder="Filter by college…"
            value={collegeFilter ? { college_id: null, college: collegeFilter } : null}
            onChange={(v) => setCollegeFilter(v?.college || '')}
          />
          <Button variant="secondary" type="submit">Search</Button>
        </form>
      )}

      {loading ? (
        <div className="dev-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="dev-card skeleton-card">
              <div className="skeleton" style={{ width: '60%', height: 20, marginBottom: 12 }} />
              <div className="skeleton" style={{ width: '90%', height: 14, marginBottom: 8 }} />
              <div className="skeleton" style={{ width: '80%', height: 14 }} />
            </div>
          ))}
        </div>
      ) : tab === 'discover' && projects.length === 0 ? (
        <Card>
          <EmptyState
            icon={<Users size={32} />}
            title="No teams yet"
            description="Be the first to create a hackathon team, or adjust your search."
            action={<Link to="/teams/new"><Button size="sm"><Plus size={14} /> Create a team</Button></Link>}
          />
        </Card>
      ) : tab === 'discover' ? (
        <>
          <div className="dev-grid">
            {projects.map((p) => <TeamCard key={p.id} project={p} />)}
          </div>
          {projects.length >= visibleLimit && (
            <div className="load-more-wrap">
              <Button variant="secondary" onClick={() => setVisibleLimit((n) => n + 20)}>
                Load more teams
              </Button>
            </div>
          )}
        </>
      ) : tab === 'mine' && myTeams.length === 0 ? (
        <Card>
          <EmptyState
            icon={<Users size={32} />}
            title="You haven't created any teams"
            description="Create a hackathon team and invite developers with matching skills."
            action={<Link to="/teams/new"><Button size="sm"><Plus size={14} /> Create a team</Button></Link>}
          />
        </Card>
      ) : tab === 'mine' ? (
        <div className="dev-grid">
          {myTeams.map((p) => <TeamCard key={p.id} project={p} />)}
        </div>
      ) : tab === 'applications' && applications.length === 0 ? (
        <Card>
          <EmptyState icon={<Send size={32} />} title="No applications" description="Teams you apply to will show up here." />
        </Card>
      ) : tab === 'applications' ? (
        <Card className="section-card">
          <div className="request-list">
            {applications.map((a) => (
              <div key={a.id} className="request-item">
                <div className="request-main">
                  <Link to={`/teams/${a.team_project_id}`} className="request-title">
                    {a.project_title || `Team #${a.team_project_id}`}
                  </Link>
                  {a.message && <p className="request-msg">"{a.message}"</p>}
                  {a.status === 'pending' && (
                    <Link to={`/teams/${a.team_project_id}`} className="fit-link">
                      Chat with the creator →
                    </Link>
                  )}
                </div>
                {statusBadge(a.status)}
              </div>
            ))}
          </div>
        </Card>
      ) : invitations.length === 0 ? (
        <Card>
          <EmptyState icon={<Inbox size={32} />} title="No invitations" description="When a team creator invites you, it will appear here." />
        </Card>
      ) : (
        <Card className="section-card">
          <div className="request-list">
            {invitations.map((inv) => (
              <div key={inv.id} className="request-item">
                <Avatar name={inv.project_title} size={40} />
                <div className="request-main">
                  <Link to={`/teams/${inv.team_project_id}`} className="request-title">
                    {inv.project_title}
                  </Link>
                  {inv.message && <p className="request-msg">"{inv.message}"</p>}
                </div>
                {inv.status === 'pending' ? (
                  <div className="request-actions">
                    <Button size="sm" disabled={respondingId === inv.id} onClick={() => handleRespondInvitation(inv.id, true)}>
                      <CheckCircle2 size={14} /> Accept
                    </Button>
                    <Button size="sm" variant="secondary" disabled={respondingId === inv.id} onClick={() => handleRespondInvitation(inv.id, false)}>
                      <XCircle size={14} /> Decline
                    </Button>
                  </div>
                ) : (
                  statusBadge(inv.status)
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

