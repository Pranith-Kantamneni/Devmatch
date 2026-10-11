import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft, MapPin, Users, Pencil, Trash2, LogOut, Send,
  CheckCircle2, XCircle, Sparkles, Code2, Layers, Link2, MessageCircle,
} from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Avatar from '../components/ui/Avatar'
import Modal from '../components/ui/Modal'
import Textarea from '../components/ui/Textarea'
import EmptyState from '../components/ui/EmptyState'
import TeamFitPanel from '../components/TeamFitPanel'
import TeamGapsPanel from '../components/TeamGapsPanel'
import TeamSettingsCard from '../components/TeamSettingsCard'
import SuggestedDevCard from '../components/SuggestedDevCard'
import TeamChatCard from '../components/TeamChatCard'
import ApplicationThread from '../components/ApplicationThread'
import { sameSkill } from '../utils/skills'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

function SuggestToolbar({
  options,
  sortBy,
  setSortBy,
  filterSkill,
  setFilterSkill,
  proofOnly,
  setProofOnly,
}) {
  return (
    <div className="suggest-toolbar">
      <div className="suggest-filter-row">
        <select
          className="input select suggest-sort"
          aria-label="Sort suggestions"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
        >
          <option value="fit">Sort: Best fit</option>
          <option value="coverage">Sort: Most coverage</option>
          <option value="stars">Sort: Most stars</option>
        </select>
        <label className="suggest-check">
          <input
            type="checkbox"
            checked={proofOnly}
            onChange={(e) => setProofOnly(e.target.checked)}
          />
          Project proof only
        </label>
      </div>
      {options.length > 0 && (
        <div className="suggest-filter-chips" role="group" aria-label="Filter by skill">
          <button
            type="button"
            className={`filter-chip ${!filterSkill ? 'active' : ''}`}
            aria-pressed={!filterSkill}
            onClick={() => setFilterSkill('')}
          >
            All skills
          </button>
          {options.map((skill) => (
            <button
              key={skill}
              type="button"
              className={`filter-chip ${filterSkill === skill ? 'active' : ''}`}
              aria-pressed={filterSkill === skill}
              onClick={() => setFilterSkill(filterSkill === skill ? '' : skill)}
            >
              {skill}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function TeamDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { toast } = useToast()

  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [recommendations, setRecommendations] = useState(null)
  const [applications, setApplications] = useState([])
  const [applyModal, setApplyModal] = useState(false)
  const [applyMessage, setApplyMessage] = useState('')
  const [acting, setActing] = useState(false)
  const [invitingId, setInvitingId] = useState(null)
  const [sortBy, setSortBy] = useState('fit')
  const [filterSkill, setFilterSkill] = useState('')
  const [proofOnly, setProofOnly] = useState(false)
  const suggestRef = useRef(null)

  const load = useCallback(async () => {
    try {
      const data = await api.getTeamProject(id)
      setProject(data)
      if (data.is_creator) {
        try {
          const recs = await api.getTeamRecommendations(id, { limit: 10 })
          setRecommendations(recs)
        } catch {
          setRecommendations(null)
        }
        try {
          setApplications(await api.listTeamApplications(id))
        } catch {
          setApplications([])
        }
      }
    } catch (err) {
      toast(err.message, 'error')
      navigate('/teams')
    } finally {
      setLoading(false)
    }
  }, [id, navigate, toast])

  useEffect(() => {
    load()
  }, [load])

  if (loading || !project) {
    return (
      <div className="page">
        <div className="skeleton" style={{ width: 120, height: 16, marginBottom: 20 }} />
        <div className="skeleton" style={{ height: 200, marginBottom: 20 }} />
        <div className="skeleton" style={{ height: 160 }} />
      </div>
    )
  }

  const spotsLeft = project.max_members - project.member_count

  const handleApply = async (e) => {
    e.preventDefault()
    setActing(true)
    try {
      await api.applyToTeam(id, { message: applyMessage || null })
      toast('Application sent')
      setApplyModal(false)
      setApplyMessage('')
      load()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setActing(false)
    }
  }

  const handleInvite = async (userId) => {
    if (invitingId) return
    setInvitingId(userId)
    try {
      await api.inviteToTeam(id, { user_id: userId })
      toast('Invitation sent')
      load()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setInvitingId(null)
    }
  }

  const handleFindSkill = (skill) => {
    setFilterSkill(skill)
    setProofOnly(false)
    suggestRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const handleApplication = async (appId, accept) => {
    try {
      if (accept) await api.acceptApplication(id, appId)
      else await api.rejectApplication(id, appId)
      toast(accept ? 'Application accepted' : 'Application rejected')
      load()
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const handleInvitationResponse = async (accept) => {
    const invId = project.invitation_status === 'pending' ? await findMyInvitationId() : null
    if (!invId) return
    try {
      if (accept) await api.acceptInvitation(invId)
      else await api.rejectInvitation(invId)
      toast(accept ? 'Welcome to the team' : 'Invitation declined')
      load()
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const findMyInvitationId = async () => {
    try {
      const invs = await api.listMyInvitations()
      const mine = invs.find(
        (i) => i.team_project_id === parseInt(id, 10) && i.status === 'pending'
      )
      return mine ? mine.id : null
    } catch {
      return null
    }
  }

  const handleRemoveMember = async (memberUserId, username) => {
    if (!window.confirm(`Remove ${username} from the team?`)) return
    try {
      await api.removeTeamMember(id, memberUserId)
      toast('Member removed')
      load()
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const handleLeave = async () => {
    if (!window.confirm('Leave this team?')) return
    try {
      await api.removeTeamMember(id, user.id)
      toast('You left the team')
      navigate('/teams')
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const handleDelete = async () => {
    if (!window.confirm('Delete this team? This cannot be undone.')) return
    try {
      await api.deleteTeamProject(id)
      toast('Team deleted')
      navigate('/teams')
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const pendingApplications = applications.filter((a) => a.status === 'pending')

  const allRecs = recommendations?.recommendations || []
  const visibleRecs = allRecs
    .filter((r) => {
      if (
        filterSkill &&
        !(r.skill_overlap || []).some((s) => sameSkill(s, filterSkill))
      ) {
        return false
      }
      if (proofOnly && !(r.skill_evidence || []).some((e) => e.project_titles.length > 0)) {
        return false
      }
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'coverage') return (b.coverage || 0) - (a.coverage || 0)
      if (sortBy === 'stars') return b.stars - a.stars || b.similarity_score - a.similarity_score
      return b.similarity_score - a.similarity_score
    })

  const clearSuggestFilters = () => {
    setFilterSkill('')
    setProofOnly(false)
    setSortBy('fit')
  }

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      toast('Team link copied — share it anywhere')
    } catch {
      toast('Could not copy the link', 'error')
    }
  }

  const requiredFilterOptions = [
    ...new Set([
      ...(project?.required_skills || []).map((s) => s.name),
      ...(project?.tech_stack || []),
    ]),
  ]

  return (
    <div className="page">
      <Link to="/teams" className="back-link">
        <ArrowLeft size={16} /> Back to teams
      </Link>

      <Card className="team-hero">
        {project.poster_url && (
          <img
            src={project.poster_url}
            alt={project.title}
            className="team-poster"
            loading="lazy"
            onError={(e) => { e.currentTarget.style.display = 'none' }}
          />
        )}
        <div className="team-hero-body">
          <div className="team-hero-top">
            <div>
              <h1 className="team-hero-title">{project.title}</h1>
              <div className="team-hero-meta">
                {project.members.length > 0 && (
                  <span className="member-stack" title={`${project.member_count} members`}>
                    {project.members.slice(0, 5).map((m) => (
                      <Avatar key={m.user_id} name={m.full_name || m.username} size={26} />
                    ))}
                    {project.members.length > 5 && (
                      <span className="member-stack-more">+{project.members.length - 5}</span>
                    )}
                  </span>
                )}
                <span className="profile-meta-item">
                  <Users size={14} /> {project.member_count}/{project.max_members} members
                </span>
                {project.kind === 'hackathon' && (
                  <Badge variant="accent">Hackathon{project.hackathon_name ? ` · ${project.hackathon_name}` : ''}</Badge>
                )}
                {project.category && (
                  <span className="profile-meta-item">{project.category}</span>
                )}
                {project.location && (
                  <span className="profile-meta-item"><MapPin size={14} /> {project.location}{project.work_mode ? ` · ${project.work_mode}` : ''}</span>
                )}
                {!project.location && project.work_mode && (
                  <span className="profile-meta-item">{project.work_mode}</span>
                )}
                {project.college && (
                  <span className="profile-meta-item"><MapPin size={14} /> {project.college}</span>
                )}
                {project.require_same_college && (
                  <Badge variant="accent">Same college only</Badge>
                )}
                {spotsLeft <= 0 && <Badge variant="neutral">Full</Badge>}
              </div>
            </div>
            <div className="team-hero-actions">
              {project.is_creator && (
                <>
                  <Link to={`/teams/${id}/edit`}><Button size="sm" variant="secondary"><Pencil size={14} /> Edit</Button></Link>
                  <Button size="sm" variant="danger" onClick={handleDelete}><Trash2 size={14} /> Delete</Button>
                </>
              )}
              {project.is_member && !project.is_creator && (
                <Button size="sm" variant="secondary" onClick={handleLeave}><LogOut size={14} /> Leave team</Button>
              )}
              {!project.is_member && !project.is_creator && project.application_status !== 'pending' && project.invitation_status !== 'pending' && (
                <Button size="sm" onClick={() => setApplyModal(true)} disabled={spotsLeft <= 0}>
                  <Send size={14} /> {spotsLeft <= 0 ? 'Team full' : 'Apply to join'}
                </Button>
              )}
              {!project.is_member && !project.is_creator && project.application_status === 'pending' && (
                <Badge variant="accent">Application pending</Badge>
              )}
              {!project.is_member && !project.is_creator && project.invitation_status === 'pending' && (
                <div className="team-invite-actions">
                  <Button size="sm" onClick={() => handleInvitationResponse(true)}>
                    <CheckCircle2 size={14} /> Accept invite
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => handleInvitationResponse(false)}>
                    <XCircle size={14} /> Decline
                  </Button>
                </div>
              )}
            </div>
          </div>

          {project.description && <p className="team-hero-desc">{project.description}</p>}

          {project.tech_stack.length > 0 && (
            <div className="team-tech">
              <Layers size={14} className="team-tech-icon" />
              {project.tech_stack.map((t) => (
                <Badge key={t} variant="neutral">{t}</Badge>
              ))}
            </div>
          )}

          {project.required_skills.length > 0 && (
            <div className="team-tech">
              <Code2 size={14} className="team-tech-icon" />
              {project.required_skills.map((s) => (
                <Badge key={s.id} variant="accent">{s.name}</Badge>
              ))}
            </div>
          )}
        </div>
      </Card>

      <div className="team-body">
        <TeamFitPanel project={project} onApply={() => setApplyModal(true)} />
        {project.is_member && project.member_count >= 2 ? (
          <TeamChatCard
            projectId={id}
            currentUsername={user?.username || ''}
            currentUserId={user?.id}
            isCreator={project.is_creator}
          />
        ) : project.is_creator ? (
          <Card className="section-card chat-locked">
            <div className="section-header">
              <div className="section-title-wrap">
                <MessageCircle size={18} className="section-icon" />
                <h3 className="section-title">Team chat</h3>
                <Badge variant="neutral">Locked</Badge>
              </div>
            </div>
            <p className="section-empty">
              Team chat (plus polls) unlocks as soon as your first teammate joins.
            </p>
            <div className="empty-action" style={{ marginTop: 12 }}>
              <Button size="sm" variant="secondary" onClick={() => suggestRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>
                Find developers below
              </Button>
            </div>
          </Card>
        ) : null}
        {!project.is_member && !project.is_creator && project.application_id && (
          <Card className="section-card">
            <div className="section-header">
              <div className="section-title-wrap">
                <MessageCircle size={18} className="section-icon" />
                <h3 className="section-title">Chat with the creator</h3>
              </div>
            </div>
            <ApplicationThread
              projectId={id}
              applicationId={project.application_id}
              currentUsername={user?.username || ''}
            />
          </Card>
        )}
        <Card className="section-card">
          <div className="section-header">
            <div className="section-title-wrap">
              <Users size={18} className="section-icon" />
              <h3 className="section-title">Members</h3>
              <span className="section-count">{project.members.length}</span>
            </div>
          </div>
          <div className="member-list">
            {project.members.map((m) => (
              <div key={m.user_id} className="member-item">
                <Link to={`/developers/${m.user_id}`} aria-label={`View ${m.username}'s profile`}>
                  <Avatar name={m.full_name || m.username} size={36} />
                </Link>
                <div className="member-info">
                  <Link to={`/developers/${m.user_id}`} className="member-name">
                    {m.full_name || m.username}
                  </Link>
                  <span className="member-username">@{m.username}</span>
                </div>
                <Badge variant={m.role === 'creator' ? 'accent' : 'neutral'}>
                  {m.role === 'creator' ? 'Creator' : 'Member'}
                </Badge>
                {project.is_creator && m.role !== 'creator' && (
                  <button className="icon-btn danger" title="Remove member" aria-label={`Remove ${m.username} from the team`} onClick={() => handleRemoveMember(m.user_id, m.username)}>
                    <Trash2 size={15} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </Card>

        {project.is_creator && (
          <>
            <TeamGapsPanel projectId={id} onFindSkill={handleFindSkill} />
            <TeamSettingsCard project={project} onSaved={load} />
            <div ref={suggestRef} className="scroll-anchor">
            <Card className="section-card">
              <div className="section-header">
                <div className="section-title-wrap">
                  <Sparkles size={18} className="section-icon" />
                  <h3 className="section-title">Suggested developers</h3>
                  {recommendations && (
                    <span className="section-count" aria-live="polite">
                      {visibleRecs.length} of {recommendations.recommendations.length}
                    </span>
                  )}
                </div>
              </div>
              {!recommendations || recommendations.recommendations.length === 0 ? (
                <div>
                  <p className="section-empty">
                    {project.required_skills.length === 0 && project.tech_stack.length === 0
                      ? 'Add required skills or tech stack to your team to unlock matched suggestions.'
                      : 'No developers match yet. Try adding more required skills — or invite developers directly from Find Teammates.'}
                  </p>
                  {project.required_skills.length === 0 && project.tech_stack.length === 0 && (
                    <div className="empty-action" style={{ marginTop: 12 }}>
                      <Link to={`/teams/${id}/edit`}><Button size="sm" variant="secondary">Add required skills</Button></Link>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <SuggestToolbar
                    options={requiredFilterOptions}
                    sortBy={sortBy}
                    setSortBy={setSortBy}
                    filterSkill={filterSkill}
                    setFilterSkill={setFilterSkill}
                    proofOnly={proofOnly}
                    setProofOnly={setProofOnly}
                  />
                  <div className="match-list">
                    {visibleRecs.map((r) => (
                      <SuggestedDevCard
                        key={r.user_id}
                        rec={r}
                        inviting={invitingId === r.user_id}
                        onInvite={handleInvite}
                      />
                    ))}
                  </div>
                  {visibleRecs.length === 0 && (
                    <p className="section-empty">
                      No suggestions match these filters.{' '}
                      <button className="link-btn" onClick={clearSuggestFilters}>Clear filters</button>
                    </p>
                  )}
                </>
              )}
            </Card>
            </div>

            <Card className="section-card">
              <div className="section-header">
                <div className="section-title-wrap">
                  <Send size={18} className="section-icon" />
                  <h3 className="section-title">Applications</h3>
                  <span className="section-count">{pendingApplications.length} pending</span>
                </div>
              </div>
              {applications.length === 0 ? (
                <div>
                  <p className="section-empty">No applications yet. Invite developers above — or share your team page so people can apply.</p>
                  <div className="empty-action" style={{ marginTop: 12 }}>
                    <Button size="sm" variant="secondary" onClick={handleCopyLink}>
                      <Link2 size={14} /> Copy team link
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="request-list">
                  {applications.map((a) => (
                    <div key={a.id} className="request-item request-item-thread">
                      <Avatar name={a.full_name || a.username} size={40} />
                      <div className="request-main">
                        <Link to={`/developers/${a.user_id}`} className="request-title">
                          {a.full_name || a.username}
                        </Link>
                        {(a.coverage > 0 || (a.matched_skills || []).length > 0) && (
                          <p className="request-fit">
                            Covers {Math.round((a.coverage || 0) * 100)}%
                            {(a.matched_skills || []).length > 0 && (
                              <> — {(a.matched_skills || []).slice(0, 3).join(', ')}</>
                            )}
                          </p>
                        )}
                        {a.message && <p className="request-msg">"{a.message}"</p>}
                        <ApplicationThread
                          projectId={id}
                          applicationId={a.id}
                          currentUsername={user?.username || ''}
                        />
                      </div>
                      {a.status === 'pending' ? (
                        <div className="request-actions">
                          <Button size="sm" onClick={() => handleApplication(a.id, true)}>
                            <CheckCircle2 size={14} /> Accept
                          </Button>
                          <Button size="sm" variant="secondary" onClick={() => handleApplication(a.id, false)}>
                            <XCircle size={14} /> Reject
                          </Button>
                        </div>
                      ) : a.status === 'accepted' ? (
                        <Badge variant="success">Accepted</Badge>
                      ) : (
                        <Badge variant="neutral">Rejected</Badge>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </>
        )}
      </div>

      <Modal
        open={applyModal}
        onClose={() => { if (!acting) setApplyModal(false) }}
        title={`Apply to ${project.title}`}
        footer={
          <>
            <Button variant="ghost" disabled={acting} onClick={() => setApplyModal(false)}>Cancel</Button>
            <Button onClick={handleApply} loading={acting}>Send application</Button>
          </>
        }
      >
        <div className="modal-form">
          <Textarea
            label="Message (optional)"
            value={applyMessage}
            onChange={(e) => setApplyMessage(e.target.value)}
            placeholder="Tell the team why you want to join and what you bring..."
          />
        </div>
      </Modal>
    </div>
  )
}
