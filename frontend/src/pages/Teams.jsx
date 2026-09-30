import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Plus, Users, Inbox, Send, Search, MapPin, CheckCircle2, XCircle,
} from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Input from '../components/ui/Input'
import EmptyState from '../components/ui/EmptyState'
import Avatar from '../components/ui/Avatar'
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
  const [tab, setTab] = useState('discover')
  const [projects, setProjects] = useState([])
  const [applications, setApplications] = useState([])
  const [invitations, setInvitations] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [collegeFilter, setCollegeFilter] = useState('')

  const loadDiscover = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (search.trim()) params.q = search.trim()
      if (collegeFilter.trim()) params.college = collegeFilter.trim()
      setProjects(await api.listTeamProjects(params))
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [toast, search, collegeFilter])

  const loadMine = useCallback(async () => {
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
  }, [toast, user.id])

  useEffect(() => {
    if (tab === 'discover') loadDiscover()
    else loadMine()
  }, [tab, loadDiscover, loadMine])

  const handleRespondInvitation = async (invId, accept) => {
    try {
      if (accept) await api.acceptInvitation(invId)
      else await api.rejectInvitation(invId)
      toast(accept ? 'Invitation accepted — welcome to the team' : 'Invitation rejected')
      loadMine()
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const myTeams = projects.filter((p) => p.creator_id === user.id)

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
        <button className={`tab ${tab === 'discover' ? 'active' : ''}`} onClick={() => setTab('discover')}>
          <Search size={15} /> Discover
        </button>
        <button className={`tab ${tab === 'mine' ? 'active' : ''}`} onClick={() => setTab('mine')}>
          <Users size={15} /> My teams
        </button>
        <button className={`tab ${tab === 'applications' ? 'active' : ''}`} onClick={() => setTab('applications')}>
          <Send size={15} /> Applications
          {applications.filter((a) => a.status === 'pending').length > 0 && (
            <span className="tab-count">{applications.filter((a) => a.status === 'pending').length}</span>
          )}
        </button>
        <button className={`tab ${tab === 'invitations' ? 'active' : ''}`} onClick={() => setTab('invitations')}>
          <Inbox size={15} /> Invitations
          {invitations.filter((i) => i.status === 'pending').length > 0 && (
            <span className="tab-count">{invitations.filter((i) => i.status === 'pending').length}</span>
          )}
        </button>
      </div>

      {tab === 'discover' && (
        <div className="teams-filters">
          <Input placeholder="Search teams..." value={search} onChange={(e) => setSearch(e.target.value)} />
          <Input placeholder="Filter by college..." value={collegeFilter} onChange={(e) => setCollegeFilter(e.target.value)} />
          <Button variant="secondary" onClick={loadDiscover}>Search</Button>
        </div>
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
        <div className="dev-grid">
          {projects.map((p) => <TeamCard key={p.id} project={p} />)}
        </div>
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
                    Team #{a.team_project_id}
                  </Link>
                  {a.message && <p className="request-msg">"{a.message}"</p>}
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
                    <Button size="sm" onClick={() => handleRespondInvitation(inv.id, true)}>
                      <CheckCircle2 size={14} /> Accept
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => handleRespondInvitation(inv.id, false)}>
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

