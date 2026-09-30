import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeft, MapPin, Users, Pencil, Trash2, LogOut, Send,
  CheckCircle2, XCircle, Sparkles, Code2, Layers,
} from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Avatar from '../components/ui/Avatar'
import Modal from '../components/ui/Modal'
import Textarea from '../components/ui/Textarea'
import EmptyState from '../components/ui/EmptyState'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

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
    try {
      await api.inviteToTeam(id, { user_id: userId })
      toast('Invitation sent')
      load()
    } catch (err) {
      toast(err.message, 'error')
    }
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

  return (
    <div className="page">
      <Link to="/teams" className="back-link">
        <ArrowLeft size={16} /> Back to teams
      </Link>

      <Card className="team-hero">
        {project.poster_url && (
          <img src={project.poster_url} alt={project.title} className="team-poster" />
        )}
        <div className="team-hero-body">
          <div className="team-hero-top">
            <div>
              <h1 className="team-hero-title">{project.title}</h1>
              <div className="team-hero-meta">
                <span className="profile-meta-item">
                  <Users size={14} /> {project.member_count}/{project.max_members} members
                </span>
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
                <Avatar name={m.full_name || m.username} size={36} />
                <div className="member-info">
                  <span className="member-name">{m.full_name || m.username}</span>
                  <span className="member-username">@{m.username}</span>
                </div>
                <Badge variant={m.role === 'creator' ? 'accent' : 'neutral'}>
                  {m.role === 'creator' ? 'Creator' : 'Member'}
                </Badge>
                {project.is_creator && m.role !== 'creator' && (
                  <button className="icon-btn danger" title="Remove member" onClick={() => handleRemoveMember(m.user_id, m.username)}>
                    <Trash2 size={15} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </Card>

        {project.is_creator && (
          <>
            <Card className="section-card">
              <div className="section-header">
                <div className="section-title-wrap">
                  <Sparkles size={18} className="section-icon" />
                  <h3 className="section-title">Suggested developers</h3>
                </div>
              </div>
              {!recommendations || recommendations.recommendations.length === 0 ? (
                <p className="section-empty">No matching developers found yet.</p>
              ) : (
                <div className="suggest-list">
                  {recommendations.recommendations.map((r) => (
                    <div key={r.user_id} className="suggest-item">
                      <Avatar name={r.full_name || r.username} size={40} />
                      <div className="suggest-info">
                        <Link to={`/developers/${r.user_id}`} className="suggest-name">
                          {r.full_name || r.username}
                        </Link>
                        <span className="suggest-score">
                          {Math.round(r.similarity_score * 100)}% match
                          {r.skill_overlap.length > 0 && ` · ${r.skill_overlap.slice(0, 3).join(', ')}`}
                        </span>
                      </div>
                      {r.invitation_status === 'pending' ? (
                        <Badge variant="accent">Invited</Badge>
                      ) : r.application_status === 'pending' ? (
                        <Badge variant="neutral">Applied</Badge>
                      ) : (
                        <Button size="sm" variant="secondary" onClick={() => handleInvite(r.user_id)}>
                          Invite
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card className="section-card">
              <div className="section-header">
                <div className="section-title-wrap">
                  <Send size={18} className="section-icon" />
                  <h3 className="section-title">Applications</h3>
                  <span className="section-count">{pendingApplications.length} pending</span>
                </div>
              </div>
              {applications.length === 0 ? (
                <p className="section-empty">No applications yet.</p>
              ) : (
                <div className="request-list">
                  {applications.map((a) => (
                    <div key={a.id} className="request-item">
                      <Avatar name={a.full_name || a.username} size={40} />
                      <div className="request-main">
                        <Link to={`/developers/${a.user_id}`} className="request-title">
                          {a.full_name || a.username}
                        </Link>
                        {a.message && <p className="request-msg">"{a.message}"</p>}
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
        onClose={() => setApplyModal(false)}
        title={`Apply to ${project.title}`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setApplyModal(false)}>Cancel</Button>
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
