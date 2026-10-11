import { useState, useEffect, useCallback, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Plus, Trash2, MapPin, Briefcase, GraduationCap, Link2,
  Code2, FolderKanban, Sparkles, Pencil, CheckCircle2, UserCheck, Upload,
  Check, X,
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
import OnboardingChecklist from '../components/OnboardingChecklist'
import CollegeSelect from '../components/CollegeSelect'
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
    <span className="proficiency" role="img" aria-label={`Proficiency ${value} out of 5`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={`prof-dot ${n <= value ? 'active' : ''}`} />
      ))}
    </span>
  )
}

/** Two-tap delete: first tap arms ("Sure?"), second confirms. No dialogs. */
function DeleteButton({ label, onDelete }) {
  const [arming, setArming] = useState(false)
  useEffect(() => {
    if (!arming) return
    const timer = setTimeout(() => setArming(false), 3000)
    return () => clearTimeout(timer)
  }, [arming])

  if (!arming) {
    return (
      <button className="icon-btn danger" onClick={() => setArming(true)} title={label} aria-label={label}>
        <Trash2 size={15} />
      </button>
    )
  }
  return (
    <span className="delete-confirm">
      <span className="delete-confirm-text">Sure?</span>
      <button
        className="icon-btn danger"
        onClick={() => { setArming(false); onDelete(); }}
        title="Yes, delete"
        aria-label="Yes, delete"
      >
        <Check size={15} />
      </button>
      <button
        className="icon-btn"
        onClick={() => setArming(false)}
        title="Keep it"
        aria-label="Cancel delete"
      >
        <X size={15} />
      </button>
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
  const [loadError, setLoadError] = useState('')
  const [editing, setEditing] = useState(false)
  const [uploading, setUploading] = useState(false)

  const [skillModal, setSkillModal] = useState(false)
  const [projectModal, setProjectModal] = useState(false)

  const loadProfile = useCallback(async () => {
    setLoadError('')
    try {
      const data = await api.getMyProfile()
      setProfile(data)
    } catch (err) {
      if (err.status === 404) {
        setProfile(null)
      } else {
        setLoadError(err.message || 'Could not load your profile')
        toast(err.message, 'error')
      }
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
    const allowed = ['.pdf', '.docx', '.txt', '.md']
    const lower = (file.name || '').toLowerCase()
    if (!allowed.some((ext) => lower.endsWith(ext)) || (lower.endsWith('.doc') && !lower.endsWith('.docx'))) {
      toast('Unsupported file type. Upload a PDF, DOCX, or TXT resume.', 'error')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      toast('File is too large. Maximum size is 10MB.', 'error')
      return
    }
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
    if (loadError) {
      return (
        <div className="page">
          <EmptyState
            icon={<UserCheck size={32} />}
            title="Could not load your profile"
            description={loadError}
            action={<Button onClick={loadProfile}>Retry</Button>}
          />
        </div>
      )
    }
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
            accept=".pdf,.docx,.txt,.md"
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
              <Avatar name={profile.full_name || user?.username || 'you'} size={80} />
              <div className="profile-card-info">
                <h2 className="profile-name">{profile.full_name || user?.username || 'Your profile'}</h2>
                <p className="profile-username">@{user?.username || 'you'}</p>
                <div className="profile-meta">
                  {profile.location && (
                    <span className="profile-meta-item"><MapPin size={13} /> {profile.location}</span>
                  )}
                  {profile.college && (
                    <span className="profile-meta-item"><GraduationCap size={13} /> {profile.college}</span>
                  )}
                  {profile.branch && (
                    <span className="profile-meta-item">{profile.branch}</span>
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
              <span className={`profile-status ${profile.availability ? 'active' : ''}`}>
                <span className="profile-status-dot" />
                {profile.availability ? 'Available for hackathons' : 'Not available right now'}
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
                      <DeleteButton label={`Remove ${s.name}`} onDelete={() => handleRemoveSkill(s.skill_id)} />
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
                        <DeleteButton label={`Remove ${p.title}`} onDelete={() => handleRemoveProject(p.id)} />
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
          <OnboardingChecklist
            profile={profile}
            actions={{
              onEdit: () => setEditing(true),
              onAddSkill: () => setSkillModal(true),
              onAddProject: () => setProjectModal(true),
              onUploadResume: () => fileInputRef.current?.click(),
            }}
          />
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
    college_id: profile?.college_id || null,
    branch: profile?.branch || '',
    experience_level: profile?.experience_level || '',
    github_url: profile?.github_url || '',
    linkedin_url: profile?.linkedin_url || '',
    portfolio_url: profile?.portfolio_url || '',
    availability: profile?.availability ?? true,
    collaboration_preferences: profile?.collaboration_preferences || '',
  })
  const [saving, setSaving] = useState(false)
  const [urlErrors, setUrlErrors] = useState({})
  const [branches, setBranches] = useState([])

  useEffect(() => {
    api
      .listBranches()
      .then((data) => setBranches(data.branches || []))
      .catch(() => setBranches([]))
  }, [])

  const set = (key) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [key]: value }))
    if (key.endsWith('_url')) {
      setUrlErrors((errs) => ({ ...errs, [key]: '' }))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const bad = {}
    for (const key of ['github_url', 'linkedin_url', 'portfolio_url']) {
      const value = (form[key] || '').trim()
      if (value && !/^https?:\/\/.+\..+/.test(value)) {
        bad[key] = 'Must start with http(s)://'
      }
    }
    setUrlErrors(bad)
    if (Object.keys(bad).length > 0) return
    setSaving(true)
    try {
      const payload = { ...form }
      if (!payload.experience_level) payload.experience_level = null
      if (!payload.branch?.trim()) payload.branch = null
      if (!payload.college?.trim() && !payload.college_id) {
        payload.college = null
        payload.college_id = null
      }
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
        <CollegeSelect
          value={form.college ? { college_id: form.college_id, college: form.college } : null}
          onChange={(v) => {
            setForm((f) => ({ ...f, college: v?.college || '', college_id: v?.college_id || null }))
          }}
          hint="Pick from 360+ colleges — powers same-college teams"
        />
        <div>
          <Input label="Branch / Department" value={form.branch} onChange={set('branch')} placeholder="e.g. Computer Science and Engineering" list="branch-options" />
          <datalist id="branch-options">
            {branches.map((b) => (
              <option key={b} value={b} />
            ))}
          </datalist>
        </div>
        <Select label="Experience level" value={form.experience_level} onChange={set('experience_level')}>
          <option value="">Select level</option>
          {EXPERIENCE_LEVELS.map((l) => (
            <option key={l.value} value={l.value}>{l.label}</option>
          ))}
        </Select>
        <Input label="GitHub URL" value={form.github_url} onChange={set('github_url')} placeholder="https://github.com/..." error={urlErrors.github_url} />
        <Input label="LinkedIn URL" value={form.linkedin_url} onChange={set('linkedin_url')} placeholder="https://linkedin.com/in/..." error={urlErrors.linkedin_url} />
        <Input label="Portfolio URL" value={form.portfolio_url} onChange={set('portfolio_url')} placeholder="https://..." error={urlErrors.portfolio_url} />
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
