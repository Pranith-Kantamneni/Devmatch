import { useState, useEffect, useCallback, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  Plus, Users, Inbox, Send, Search, MapPin, CheckCircle2, XCircle,
  SlidersHorizontal, X, Trophy,
} from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import EmptyState from '../components/ui/EmptyState'
import Avatar from '../components/ui/Avatar'
import CollegeSelect from '../components/CollegeSelect'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { PROJECT_CATEGORIES } from '../utils/constants'

function statusBadge(status) {
  if (status === 'accepted') return <Badge variant="success">Accepted</Badge>
  if (status === 'rejected') return <Badge variant="neutral">Rejected</Badge>
  return <Badge variant="accent">Pending</Badge>
}

function TeamCard({ project }) {
  const spotsLeft = project.max_members - project.member_count
  const isHackathon = project.kind === 'hackathon'
  return (
    <Link to={`/teams/${project.id}`} className="dev-card">
      <div className="dev-card-top">
        <div className="team-card-avatar">
          {isHackathon ? <Trophy size={22} /> : <Users size={22} />}
        </div>
        <div className="dev-card-id">
          <h3 className="dev-card-name">{project.title}</h3>
          <p className="dev-card-username">
            {project.member_count}/{project.max_members} members
            {spotsLeft <= 0 ? ' · Full' : ` · ${spotsLeft} spot${spotsLeft === 1 ? '' : 's'} left`}
          </p>
        </div>
        {(project.match_coverage || 0) > 0 && (
          <span className="team-match-badge" title="How well this team matches your skills">
            {Math.round(project.match_coverage * 100)}%
          </span>
        )}
      </div>

      {project.hackathon_name && (
        <p className="team-hackathon"><Trophy size={13} /> {project.hackathon_name}</p>
      )}
      {project.description && <p className="dev-card-bio">{project.description}</p>}

      <div className="dev-card-meta">
        <Badge variant={isHackathon ? 'accent' : 'neutral'}>{isHackathon ? 'Hackathon' : 'Project'}</Badge>
        {project.category && <Badge variant="neutral">{project.category}</Badge>}
        {project.location && (
          <span className="dev-card-meta-item"><MapPin size={13} /> {project.location}</span>
        )}
        {project.work_mode && (
          <span className="dev-card-meta-item">{project.work_mode}</span>
        )}
        {project.college && (
          <span className="dev-card-meta-item">{project.college}</span>
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

const EMPTY_FILTERS = {
  q: '',
  college: '',
  tech: [],
  match_my_stack: false,
  location: '',
  work_mode: '',
  category: '',
  hackathon: '',
  kind: '',
  open_only: false,
  sort: 'newest',
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
  const [createdTeams, setCreatedTeams] = useState([])
  const [joinedTeams, setJoinedTeams] = useState([])
  const [applications, setApplications] = useState([])
  const [invitations, setInvitations] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [applied, setApplied] = useState(EMPTY_FILTERS)
  const [visibleLimit, setVisibleLimit] = useState(20)
  const [respondingId, setRespondingId] = useState(null)
  const [myTech, setMyTech] = useState([])
  const [showFilters, setShowFilters] = useState(false)
  const [techInput, setTechInput] = useState('')
  const searchTimer = useRef(null)

  // My skill names power "match my stack" hints + tech suggestions.
  useEffect(() => {
    api
      .getMyProfile()
      .then((p) => setMyTech((p.skills || []).map((s) => s.name)))
      .catch(() => {})
  }, [])

  // Debounce free-text fields so we don't spam the API per keystroke.
  useEffect(() => {
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => {
      setApplied((prev) => ({
        ...prev,
        q: filters.q.trim(),
        location: filters.location.trim(),
        hackathon: filters.hackathon.trim(),
      }))
      setVisibleLimit(20)
    }, 400)
    return () => clearTimeout(searchTimer.current)
  }, [filters.q, filters.location, filters.hackathon])

  const setF = (patch, immediate = false) => {
    setFilters((f) => ({ ...f, ...patch }))
    if (immediate) {
      setApplied((prev) => ({ ...prev, ...patch }))
      setVisibleLimit(20)
    }
  }

  const loadDiscover = useCallback(async () => {
    setLoading(true)
    try {
      const params = { limit: visibleLimit, sort: applied.sort }
      for (const key of ['q', 'college', 'location', 'work_mode', 'category', 'hackathon', 'kind']) {
        if (applied[key]) params[key] = applied[key]
      }
      if (applied.tech.length > 0) params.tech = applied.tech
      if (applied.match_my_stack) params.match_my_stack = true
      if (applied.open_only) params.open_only = true
      setProjects(await api.listTeamProjects(params))
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [toast, applied, visibleLimit])

  const loadMine = useCallback(async () => {
    if (!user?.id) return
    setLoading(true)
    try {
      const [all, joined, apps, invs] = await Promise.all([
        api.listTeamProjects({ limit: 100 }),
        api.listJoinedTeams(),
        api.listMyApplications(),
        api.listMyInvitations(),
      ])
      setCreatedTeams(all.filter((p) => p.creator_id === user.id))
      setJoinedTeams(joined)
      setApplications(apps)
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

  const addTech = (raw) => {
    const name = (raw || '').trim()
    if (!name) return
    setTechInput('')
    if (filters.tech.some((t) => t.toLowerCase() === name.toLowerCase())) return
    setF({ tech: [...filters.tech, name] }, true)
  }

  const activeChips = []
  if (applied.q) activeChips.push({ key: 'q', label: `"${applied.q}"`, clear: () => setFilters((f) => ({ ...f, q: '' })) })
  if (applied.college) activeChips.push({ key: 'college', label: applied.college, clear: () => setF({ college: '' }, true) })
  applied.tech.forEach((t) => activeChips.push({ key: `tech-${t}`, label: t, clear: () => setF({ tech: filters.tech.filter((x) => x !== t) }, true) }))
  if (applied.match_my_stack) activeChips.push({ key: 'mystack', label: 'Matches my stack', clear: () => setF({ match_my_stack: false }, true) })
  if (applied.location) activeChips.push({ key: 'location', label: applied.location, clear: () => setFilters((f) => ({ ...f, location: '' })) })
  if (applied.work_mode) activeChips.push({ key: 'work_mode', label: applied.work_mode, clear: () => setF({ work_mode: '' }, true) })
  if (applied.category) activeChips.push({ key: 'category', label: applied.category, clear: () => setF({ category: '' }, true) })
  if (applied.hackathon) activeChips.push({ key: 'hackathon', label: applied.hackathon, clear: () => setFilters((f) => ({ ...f, hackathon: '' })) })
  if (applied.kind) activeChips.push({ key: 'kind', label: applied.kind === 'hackathon' ? 'Hackathons' : 'Projects', clear: () => setF({ kind: '' }, true) })
  if (applied.open_only) activeChips.push({ key: 'open_only', label: 'Has openings', clear: () => setF({ open_only: false }, true) })

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS)
    setApplied(EMPTY_FILTERS)
    setTechInput('')
    setVisibleLimit(20)
  }

  const hasMine = createdTeams.length > 0 || joinedTeams.length > 0

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
        <div className="discover-filters">
          <div className="discover-topbar">
            <div className="discover-search">
              <Search size={15} className="discover-search-icon" />
              <input
                className="input"
                placeholder="Search teams, hackathons…"
                aria-label="Search teams"
                value={filters.q}
                onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
              />
            </div>
            <div className="kind-chips" role="group" aria-label="Team type">
              {[
                { value: '', label: 'All' },
                { value: 'hackathon', label: 'Hackathons' },
                { value: 'project', label: 'Projects' },
              ].map((k) => (
                <button
                  key={k.value}
                  className={`filter-chip ${applied.kind === k.value ? 'active' : ''}`}
                  onClick={() => setF({ kind: k.value }, true)}
                >
                  {k.label}
                </button>
              ))}
            </div>
            <select
              className="input select discover-sort"
              aria-label="Sort teams"
              value={applied.sort}
              onChange={(e) => setF({ sort: e.target.value }, true)}
            >
              <option value="newest">Newest</option>
              <option value="relevance">Best match</option>
              <option value="tech_match">Tech match</option>
            </select>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowFilters((v) => !v)}
              aria-expanded={showFilters}
            >
              <SlidersHorizontal size={14} /> Filters
              {activeChips.length > 0 && <span className="tab-count">{activeChips.length}</span>}
            </Button>
          </div>

          {showFilters && (
            <Card className="section-card filter-panel">
              <div className="filter-grid">
                <div className="field">
                  <label className="field-label">Tech stack (any match)</label>
                  <div className="team-skill-add">
                    <input
                      className="input"
                      placeholder="e.g. Python"
                      aria-label="Add technology filter"
                      value={techInput}
                      list="tech-suggestions"
                      onChange={(e) => setTechInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          addTech(techInput)
                        }
                      }}
                    />
                    <datalist id="tech-suggestions">
                      {myTech.map((t) => (
                        <option key={t} value={t} />
                      ))}
                    </datalist>
                    <Button type="button" size="sm" variant="secondary" onClick={() => addTech(techInput)}>
                      Add
                    </Button>
                  </div>
                  {filters.tech.length > 0 && (
                    <div className="team-skill-chips" style={{ marginTop: 8 }}>
                      {filters.tech.map((t) => (
                        <span key={t} className="team-skill-chip">
                          {t}
                          <button
                            type="button"
                            className="team-skill-remove"
                            aria-label={`Remove ${t} filter`}
                            onClick={() => setF({ tech: filters.tech.filter((x) => x !== t) }, true)}
                          >
                            <X size={13} />
                          </button>
                        </span>
                      ))}
                    </div>
                  )}
                  <label className="suggest-check" style={{ marginTop: 8 }}>
                    <input
                      type="checkbox"
                      checked={filters.match_my_stack}
                      onChange={(e) => setF({ match_my_stack: e.target.checked }, true)}
                    />
                    Match my tech stack ({myTech.length} skills)
                  </label>
                </div>
                <CollegeSelect
                  label="College"
                  placeholder="Any college…"
                  value={filters.college ? { college_id: null, college: filters.college } : null}
                  onChange={(v) => setF({ college: v?.college || '' }, true)}
                />
                <Input
                  label="Location"
                  placeholder="City, e.g. Chennai"
                  value={filters.location}
                  onChange={(e) => setFilters((f) => ({ ...f, location: e.target.value }))}
                />
                <Select
                  label="Work mode"
                  value={filters.work_mode}
                  onChange={(e) => setF({ work_mode: e.target.value }, true)}
                >
                  <option value="">Any mode</option>
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="onsite">On-site</option>
                </Select>
                <Select
                  label="Category"
                  value={filters.category}
                  onChange={(e) => setF({ category: e.target.value }, true)}
                >
                  <option value="">All categories</option>
                  {PROJECT_CATEGORIES.filter((c) => c !== 'Other').map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </Select>
                <Input
                  label="Hackathon"
                  placeholder="Event name"
                  value={filters.hackathon}
                  onChange={(e) => setFilters((f) => ({ ...f, hackathon: e.target.value }))}
                />
              </div>
              <label className="suggest-check">
                <input
                  type="checkbox"
                  checked={filters.open_only}
                  onChange={(e) => setF({ open_only: e.target.checked }, true)}
                />
                Only teams with open spots
              </label>
            </Card>
          )}

          {activeChips.length > 0 && (
            <div className="active-chips">
              {activeChips.map((c) => (
                <span key={c.key} className="team-skill-chip">
                  {c.label}
                  <button
                    type="button"
                    className="team-skill-remove"
                    aria-label={`Remove ${c.label} filter`}
                    onClick={c.clear}
                  >
                    <X size={13} />
                  </button>
                </span>
              ))}
              <button className="link-btn" onClick={clearFilters}>Clear all</button>
            </div>
          )}
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
            title="No teams match"
            description="Try widening your filters — or be the first to create a team for this search."
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
      ) : tab === 'mine' && !hasMine ? (
        <Card>
          <EmptyState
            icon={<Users size={32} />}
            title="No teams yet"
            description="Create a hackathon team — or apply to one in Discover to see it here."
            action={<Link to="/teams/new"><Button size="sm"><Plus size={14} /> Create a team</Button></Link>}
          />
        </Card>
      ) : tab === 'mine' ? (
        <>
          {createdTeams.length > 0 && (
            <div className="mine-section">
              <h3 className="mine-section-title">Created by you ({createdTeams.length})</h3>
              <div className="dev-grid">
                {createdTeams.map((p) => <TeamCard key={p.id} project={p} />)}
              </div>
            </div>
          )}
          {joinedTeams.length > 0 && (
            <div className="mine-section">
              <h3 className="mine-section-title">Teams you joined ({joinedTeams.length})</h3>
              <div className="dev-grid">
                {joinedTeams.map((p) => <TeamCard key={p.id} project={p} />)}
              </div>
            </div>
          )}
        </>
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
