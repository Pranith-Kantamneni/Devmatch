import { useState, useEffect, useCallback, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Plus, Trash2, MapPin, Briefcase, GraduationCap, Link2,
  Code2, FolderKanban, Sparkles, Pencil, CheckCircle2, UserCheck, Upload,
} from 'lucide-react'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Textarea from '../components/ui/Textarea'
import Select from '../components/ui/Select'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Avatar from '../components/ui/Avatar'
import Modal from '../components/ui/Modal'
import EmptyState from '../components/ui/EmptyState'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const EXPERIENCE_LEVELS = [
  { value: 'student', label: 'Student' },
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid-level' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead' },
]

const SKILL_CATEGORIES = [
  { value: 'language', label: 'Language' },
  { value: 'framework', label: 'Framework' },
  { value: 'tool', label: 'Tool' },
  { value: 'domain', label: 'Domain' },
  { value: 'other', label: 'Other' },
]

function ProficiencyDots({ value }) {
  return (
    <span className="proficiency">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={`prof-dot ${n <= value ? 'active' : ''}`} />
      ))}
    </span>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(false)
  const [uploading, setUploading] = useState(false)

  const [skillModal, setSkillModal] = useState(false)
  const [projectModal, setProjectModal] = useState(false)

  const loadProfile = useCallback(async () => {
    try {
      const data = await api.getMyProfile()
      setProfile(data)
    } catch (err) {
      if (err.status !== 404) toast(err.message, 'error')
      setProfile(null)
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  const handleRemoveSkill = async (skillId) => {
    try {
      await api.removeSkill(skillId)
      toast('Skill removed')
      loadProfile()
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const handleRemoveProject = async (projectId) => {
    try {
      await api.removeProject(projectId)
      toast('Project removed')
      loadProfile()
    } catch (err) {
      toast(err.message, 'error')
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''
    handleUpload(file)
  }

  const handleUpload = async (file) => {
    setUploading(true)
    try {
      const parsed = await api.parseResume(file)
      navigate('/review-resume', { state: { parsed } })
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setUploading(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="page-header-skeleton">
          <div className="skeleton" style={{ width: 200, height: 28 }} />
          <div className="skeleton" style={{ width: 320, height: 16 }} />
        </div>
        <div className="dashboard-grid">
          <div className="skeleton" style={{ height: 340 }} />
          <div className="skeleton" style={{ height: 340 }} />
        </div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="page">
        <EmptyState
          icon={<UserCheck size={32} />}
          title="Set up your teammate profile"
          description="Add your skills and projects so other developers can find and match with you for hackathons."
          action={<Button onClick={() => setEditing(true)}><Pencil size={15} /> Create your profile</Button>}
        />
        <ProfileEditor
          profile={null}
          onSaved={(p) => { setProfile(p); setEditing(false) }}
          open={editing}
          onClose={() => setEditing(false)}
        />
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-header-text">
          <h1 className="page-title">My teammate profile</h1>
          <p className="page-subtitle">This is how other developers will find and match with you</p>
        </div>
        <div className="page-header-actions">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt,.md"
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />
          <Button variant="secondary" onClick={() => fileInputRef.current?.click()} loading={uploading}>
            <Upload size={15} />
            {uploading ? 'Parsing...' : 'Upload resume'}
          </Button>
          <Button variant="secondary" onClick={() => setEditing((v) => !v)}>
            <Pencil size={15} />
            {editing ? 'Done' : 'Edit profile'}
          </Button>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-main">
          <Card className="profile-card">
            <div className="profile-card-header">
              <Avatar name={profile.full_name || user.username} size={72} />
              <div className="profile-card-info">
                <h2 className="profile-name">{profile.full_name || user.username}</h2>
                <p className="profile-username">@{user.username}</p>
                <div className="profile-meta">
                  {profile.location && (
                    <span className="profile-meta-item"><MapPin size={13} /> {profile.location}</span>
                  )}
                  {profile.experience_level && (
                    <span className="profile-meta-item">
                      <Briefcase size={13} /> {EXPERIENCE_LEVELS.find((l) => l.value === profile.experience_level)?.label}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {profile.bio && <p className="profile-bio">{profile.bio}</p>}

            <div className="profile-status-row">
              <span className={`profile-status ${profile.available ? 'active' : ''}`}>
                <span className="profile-status-dot" />
                {profile.available ? 'Available for hackathons' : 'Not available right now'}
              </span>
            </div>

            <div className="profile-links">
              {profile.github_url && (
                <a href={profile.github_url} target="_blank" rel="noreferrer" className="profile-link">
                  <Link2 size={14} /> GitHub
                </a>
              )}
              {profile.linkedin_url && (
                <a href={profile.linkedin_url} target="_blank" rel="noreferrer" className="profile-link">
                  <Link2 size={14} /> LinkedIn
                </a>
              )}
              {profile.portfolio_url && (
                <a href={profile.portfolio_url} target="_blank" rel="noreferrer" className="profile-link">
                  <Link2 size={14} /> Portfolio
                </a>
              )}
            </div>

            {editing && (
              <ProfileEditor
                profile={profile}
                onSaved={(p) => { setProfile(p); setEditing(false) }}
              />
            )}
          </Card>

          <Card className="section-card">
            <div className="section-header">
              <div className="section-title-wrap">
                <Code2 size={18} className="section-icon" />
                <h3 className="section-title">Your tech stack</h3>
                <span className="section-count">{profile.skills.length}</span>
              </div>
              <Button size="sm" variant="secondary" onClick={() => setSkillModal(true)}>
                <Plus size={14} /> Add skill
              </Button>
            </div>
            {profile.skills.length === 0 ? (
              <EmptyState
                icon={<Code2 size={28} />}
                title="No skills yet"
                description="Add your skills so DevMatch can find teammates with complementary expertise."
                action={<Button size="sm" onClick={() => setSkillModal(true)}><Plus size={14} /> Add your first skill</Button>}
              />
            ) : (
              <div className="skill-list">
                {profile.skills.map((s) => (
                  <div key={s.skill_id} className="skill-item">
                    <div className="skill-item-main">
                      <span className="skill-name">{s.name}</span>
                      <Badge variant="neutral">{SKILL_CATEGORIES.find((c) => c.value === s.category)?.label}</Badge>
                    </div>
                    <div className="skill-item-side">
                      <ProficiencyDots value={s.proficiency} />
                      <button className="icon-btn danger" onClick={() => handleRemoveSkill(s.skill_id)} title="Remove skill">
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="section-card">
            <div className="section-header">
              <div className="section-title-wrap">
                <FolderKanban size={18} className="section-icon" />
                <h3 className="section-title">Your projects</h3>
                <span className="section-count">{profile.projects.length}</span>
              </div>
              <Button size="sm" variant="secondary" onClick={() => setProjectModal(true)}>
                <Plus size={14} /> Add project
              </Button>
            </div>
            {profile.projects.length === 0 ? (
              <EmptyState
                icon={<FolderKanban size={28} />}
                title="No projects yet"
                description="Showcase projects you're proud of — they strengthen your teammate matches."
                action={<Button size="sm" onClick={() => setProjectModal(true)}><Plus size={14} /> Add your first project</Button>}
              />
            ) : (
              <div className="project-list">
                {profile.projects.map((p) => (
                  <div key={p.id} className="project-item">
                    <div className="project-item-main">
                      <div className="project-item-top">
                        <span className="project-title">{p.title}</span>
                        <button className="icon-btn danger" onClick={() => handleRemoveProject(p.id)} title="Remove project">
                          <Trash2 size={15} />
                        </button>
                      </div>
                      {p.description && <p className="project-desc">{p.description}</p>}
                      {p.skills.length > 0 && (
                        <div className="project-skills">
                          {p.skills.map((s) => (
                            <Badge key={s.id} variant="accent">{s.name}</Badge>
                          ))}
                        </div>
                      )}
                    </div>
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
                  <h3 className="section-title">What I'm looking for in a team</h3>
                </div>
              </div>
              <p className="section-text">{profile.collaboration_preferences}</p>
            </Card>
          )}
        </div>

        <div className="dashboard-side">
          <Card className="side-card">
            <div className="side-card-header">
              <Sparkles size={18} className="side-icon" />
              <h3 className="side-title">Match readiness</h3>
            </div>
            <ReadinessMeter profile={profile} />
            <ReadinessTips profile={profile} />
          </Card>

          <Card className="side-card">
            <h3 className="side-title">Profile completeness</h3>
            <CompletenessMeter profile={profile} />
          </Card>

          <Link to="/teammates" className="side-cta">
            <div className="side-cta-icon"><UserCheck size={18} /></div>
            <div className="side-cta-text">
              <span className="side-cta-title">Find your teammates</span>
              <span className="side-cta-sub">See who matches your stack</span>
            </div>
          </Link>
        </div>
      </div>

      <SkillModal
        open={skillModal}
        onClose={() => setSkillModal(false)}
        onAdded={() => { setSkillModal(false); loadProfile(); }}
      />
      <ProjectModal
        open={projectModal}
        onClose={() => setProjectModal(false)}
        onAdded={() => { setProjectModal(false); loadProfile(); }}
      />
    </div>
  )
}

function ProfileEditor({ profile, onSaved, open = true, onClose }) {
  const { toast } = useToast()
  const [form, setForm] = useState({
    full_name: profile?.full_name || '',
    bio: profile?.bio || '',
    location: profile?.location || '',
    education: profile?.education || '',
    college: profile?.college || '',
    experience_level: profile?.experience_level || '',
    github_url: profile?.github_url || '',
    linkedin_url: profile?.linkedin_url || '',
    portfolio_url: profile?.portfolio_url || '',
    availability: profile?.availability ?? true,
    collaboration_preferences: profile?.collaboration_preferences || '',
  })
  const [saving, setSaving] = useState(false)

  const set = (key) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [key]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = { ...form }
      if (!payload.experience_level) payload.experience_level = null
      const updated = await api.updateProfile(payload)
      toast('Profile updated')
      onSaved(updated)
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <form onSubmit={handleSubmit} className="profile-editor">
      <div className="profile-editor-grid">
        <Input label="Full name" value={form.full_name} onChange={set('full_name')} placeholder="Your name" />
        <Input label="Location" value={form.location} onChange={set('location')} placeholder="City, Country" />
        <Input label="Education" value={form.education} onChange={set('education')} placeholder="Degree, institution" />
        <Input label="College" value={form.college} onChange={set('college')} placeholder="e.g. MIT — used for same-college teams" />
        <Select label="Experience level" value={form.experience_level} onChange={set('experience_level')}>
          <option value="">Select level</option>
          {EXPERIENCE_LEVELS.map((l) => (
            <option key={l.value} value={l.value}>{l.label}</option>
          ))}
        </Select>
        <Input label="GitHub URL" value={form.github_url} onChange={set('github_url')} placeholder="https://github.com/..." />
        <Input label="LinkedIn URL" value={form.linkedin_url} onChange={set('linkedin_url')} placeholder="https://linkedin.com/in/..." />
        <Input label="Portfolio URL" value={form.portfolio_url} onChange={set('portfolio_url')} placeholder="https://..." />
      </div>

      <label className="toggle-row">
        <input type="checkbox" checked={form.availability} onChange={set('availability')} />
        <span className="toggle-label">
          <span className="toggle-title">Available for hackathons</span>
          <span className="toggle-desc">Let others know you're open to joining a team</span>
        </span>
      </label>

      <Textarea label="Bio" value={form.bio} onChange={set('bio')} placeholder="Tell developers what you work on and care about" />
      <Textarea
        label="What I'm looking for in a team"
        value={form.collaboration_preferences}
        onChange={set('collaboration_preferences')}
        placeholder="e.g. Looking for a designer and a backend dev for a 48-hour hackathon..."
      />
      <div className="profile-editor-actions">
        {onClose && <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>}
        <Button type="submit" loading={saving}>Save changes</Button>
      </div>
    </form>
  )
}

function SkillModal({ open, onClose, onAdded }) {
  const { toast } = useToast()
  const [name, setName] = useState('')
  const [category, setCategory] = useState('language')
  const [proficiency, setProficiency] = useState(3)
  const [years, setYears] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.addSkill({
        name,
        category,
        proficiency,
        years_experience: years ? parseFloat(years) : null,
      })
      toast('Skill added')
      setName(''); setProficiency(3); setYears('')
      onAdded()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Add a skill"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" form="skill-form" loading={saving}>Add skill</Button>
        </>
      }
    >
      <form id="skill-form" onSubmit={handleSubmit} className="modal-form">
        <Input label="Skill" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Python, React, Kubernetes" required autoFocus />
        <div className="modal-form-row">
          <Select label="Category" value={category} onChange={(e) => setCategory(e.target.value)}>
            {SKILL_CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </Select>
          <Input label="Years (optional)" type="number" min="0" step="0.5" value={years} onChange={(e) => setYears(e.target.value)} placeholder="3" />
        </div>
        <div className="field">
          <label className="field-label">Proficiency — {proficiency}/5</label>
          <input type="range" min="1" max="5" value={proficiency} onChange={(e) => setProficiency(parseInt(e.target.value))} className="range-input" />
        </div>
      </form>
    </Modal>
  )
}

function ProjectModal({ open, onClose, onAdded }) {
  const { toast } = useToast()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [url, setUrl] = useState('')
  const [skillNames, setSkillNames] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.addProject({
        title,
        description: description || null,
        url: url || null,
        skill_names: skillNames.split(',').map((s) => s.trim()).filter(Boolean),
      })
      toast('Project added')
      setTitle(''); setDescription(''); setUrl(''); setSkillNames('')
      onAdded()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Add a project"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" form="project-form" loading={saving}>Add project</Button>
        </>
      }
    >
      <form id="project-form" onSubmit={handleSubmit} className="modal-form">
        <Input label="Title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Real-time collaboration tool" required autoFocus />
        <Textarea label="Description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What does it do? What was your role?" />
        <Input label="URL (optional)" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://..." />
        <Input
          label="Skills used (comma-separated)"
          value={skillNames}
          onChange={(e) => setSkillNames(e.target.value)}
          placeholder="e.g. Python, FastAPI, PostgreSQL"
          hint="These become part of your matching profile"
        />
      </form>
    </Modal>
  )
}

function ReadinessMeter({ profile }) {
  const hasSkills = profile.skills.length > 0
  const hasProjects = profile.projects.length > 0
  const hasBio = !!profile.bio
  const hasLevel = !!profile.experience_level
  const score = [hasSkills, hasProjects, hasBio, hasLevel].filter(Boolean).length

  return (
    <div className="readiness-meter">
      <div className="readiness-bar">
        <div className="readiness-fill" style={{ width: `${(score / 4) * 100}%` }} />
      </div>
      <p className="readiness-label">{score}/4 signals active</p>
    </div>
  )
}

function ReadinessTips({ profile }) {
  const tips = []
  if (!profile.skills.length) tips.push('Add skills to improve matches')
  if (!profile.projects.length) tips.push('Add a project to stand out')
  if (!profile.bio) tips.push('Write a short bio')
  if (!profile.experience_level) tips.push('Set your experience level')

  if (tips.length === 0) {
    return <p className="readiness-good">Your profile is ready for matching.</p>
  }
  return (
    <ul className="readiness-tips">
      {tips.map((tip) => (
        <li key={tip}>{tip}</li>
      ))}
    </ul>
  )
}

function CompletenessMeter({ profile }) {
  const fields = [
    { label: 'Bio', done: !!profile.bio },
    { label: 'Location', done: !!profile.location },
    { label: 'Experience level', done: !!profile.experience_level },
    { label: 'GitHub', done: !!profile.github_url },
    { label: 'LinkedIn', done: !!profile.linkedin_url },
    { label: 'Portfolio', done: !!profile.portfolio_url },
    { label: 'Education', done: !!profile.education },
  ]
  const done = fields.filter((f) => f.done).length
  const pct = Math.round((done / fields.length) * 100)

  return (
    <div className="completeness">
      <div className="completeness-bar">
        <div className="completeness-fill" style={{ width: `${pct}%` }} />
      </div>
      <p className="completeness-label">{pct}% complete</p>
    </div>
  )
}
