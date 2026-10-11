import { useState, useEffect } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { ArrowLeft, Plus, Trash2 } from 'lucide-react'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Textarea from '../components/ui/Textarea'
import Select from '../components/ui/Select'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'
import CollegeSelect from '../components/CollegeSelect'
import { PROJECT_CATEGORIES } from '../utils/constants'

const SKILL_CATEGORIES = [
  { value: 'language', label: 'Language' },
  { value: 'framework', label: 'Framework' },
  { value: 'tool', label: 'Tool' },
  { value: 'domain', label: 'Domain' },
  { value: 'other', label: 'Other' },
]

export default function TeamForm({ mode }) {
  const { id } = useParams()
  const navigate = useNavigate()
  const { toast } = useToast()
  const isEdit = mode === 'edit'

  const [form, setForm] = useState({
    title: '',
    description: '',
    tech_stack_input: '',
    required_skills: [],
    poster_url: '',
    max_members: 4,
    college: '',
    college_id: null,
    require_same_college: false,
    kind: 'project',
    category: '',
    hackathon_name: '',
    location: '',
    work_mode: '',
  })
  const [skillName, setSkillName] = useState('')
  const [skillCategory, setSkillCategory] = useState('language')
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!isEdit) return
    api
      .getTeamProject(id)
      .then((p) => {
        setForm({
          title: p.title,
          description: p.description || '',
          tech_stack_input: (p.tech_stack || []).join(', '),
          required_skills: (p.required_skills || []).map((s) => ({
            name: s.name,
            category: s.category,
          })),
          poster_url: p.poster_url || '',
          max_members: p.max_members,
          college: p.college || '',
          college_id: p.college_id || null,
          require_same_college: p.require_same_college,
          kind: p.kind || 'project',
          category: p.category || '',
          hackathon_name: p.hackathon_name || '',
          location: p.location || '',
          work_mode: p.work_mode || '',
        })
      })
      .catch((err) => {
        toast(err.message, 'error')
        navigate('/teams')
      })
      .finally(() => setLoading(false))
  }, [isEdit, id, navigate, toast])

  const set = (key) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [key]: value }))
  }

  const addSkill = () => {
    const name = skillName.trim()
    if (!name) return
    if (form.required_skills.some((s) => s.name.toLowerCase() === name.toLowerCase())) {
      toast('Skill already added', 'error')
      return
    }
    setForm((f) => ({
      ...f,
      required_skills: [...f.required_skills, { name, category: skillCategory }],
    }))
    setSkillName('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) {
      toast('Give your team a name', 'error')
      return
    }
    if (form.require_same_college && !form.college.trim() && !form.college_id) {
      toast('College is required when same-college is enabled', 'error')
      return
    }
    let maxMembers = parseInt(form.max_members, 10)
    if (!Number.isFinite(maxMembers)) {
      toast('Enter a valid team size (2–50)', 'error')
      return
    }
    maxMembers = Math.min(50, Math.max(2, maxMembers))
    const poster = form.poster_url.trim()
    if (poster && !/^https?:\/\/.+\..+/.test(poster)) {
      toast('Poster URL must start with http(s)://', 'error')
      return
    }
    setSaving(true)
    try {
      const payload = {
        title: form.title.trim(),
        description: form.description.trim() || null,
        tech_stack: form.tech_stack_input.split(',').map((t) => t.trim()).filter(Boolean),
        required_skills: form.required_skills,
        poster_url: poster || null,
        max_members: maxMembers,
        college: form.college.trim() || null,
        college_id: form.college_id || null,
        require_same_college: form.require_same_college,
        kind: form.kind,
        category: form.category || null,
        hackathon_name: form.kind === 'hackathon' ? (form.hackathon_name.trim() || null) : null,
        location: form.location.trim() || null,
        work_mode: form.work_mode || null,
      }
      if (isEdit) {
        await api.updateTeamProject(id, payload)
        toast('Team updated')
        navigate(`/teams/${id}`)
      } else {
        const created = await api.createTeamProject(payload)
        toast('Team created')
        navigate(`/teams/${created.id}`)
      }
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="skeleton" style={{ width: 200, height: 28, marginBottom: 20 }} />
        <div className="skeleton" style={{ height: 400 }} />
      </div>
    )
  }

  return (
    <div className="page">
      <Link to={isEdit ? `/teams/${id}` : '/teams'} className="back-link">
        <ArrowLeft size={16} /> Back to teams
      </Link>

      <div className="page-header">
        <div className="page-header-text">
          <h1 className="page-title">{isEdit ? 'Edit team' : 'Create a team'}</h1>
          <p className="page-subtitle">
            {isEdit ? 'Update your hackathon team details' : 'Start a hackathon team and find developers with matching skills'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="team-form-grid">
          <Card className="review-card">
            <div className="review-section-header">
              <h3 className="review-section-title">Basics</h3>
            </div>
            <div className="review-form">
              <div className="team-kind-row" role="group" aria-label="Team type">
                {[
                  { value: 'project', label: 'Project team' },
                  { value: 'hackathon', label: 'Hackathon team' },
                ].map((k) => (
                  <button
                    key={k.value}
                    type="button"
                    className={`filter-chip ${form.kind === k.value ? 'active' : ''}`}
                    onClick={() => setForm((f) => ({ ...f, kind: k.value }))}
                  >
                    {k.label}
                  </button>
                ))}
              </div>
              <Input label="Team name" value={form.title} onChange={set('title')} placeholder="e.g. AI Builders Hackathon Team" required maxLength={200} />
              <Textarea label="Description" value={form.description} onChange={set('description')} placeholder="What will you build? What is the goal?" />
              {form.kind === 'hackathon' && (
                <Input label="Hackathon name" value={form.hackathon_name} onChange={set('hackathon_name')} placeholder="e.g. HackNight 2026" maxLength={200} />
              )}
              <Input label="Poster / image URL (optional)" value={form.poster_url} onChange={set('poster_url')} placeholder="https://..." hint="Shown at the top of your team page" />
              {form.poster_url.trim() && /^https?:\/\/.+\..+/.test(form.poster_url.trim()) && (
                <div className="poster-preview">
                  <img
                    src={form.poster_url.trim()}
                    alt="Team poster preview"
                    loading="lazy"
                    onError={(e) => { e.currentTarget.style.display = 'none' }}
                  />
                </div>
              )}
              <Input label="Tech stack (comma-separated)" value={form.tech_stack_input} onChange={set('tech_stack_input')} placeholder="e.g. Python, React, PostgreSQL" hint="Free-form technologies used by the team" />
            </div>
          </Card>

          <Card className="review-card">
            <div className="review-section-header">
              <h3 className="review-section-title">Required skills</h3>
              <span className="section-count">{form.required_skills.length}</span>
            </div>
            <p className="section-empty" style={{ marginBottom: 12 }}>
              Used to match developers to your team. Categories improve match quality.
            </p>
            <div className="team-skill-add">
              <input
                className="input"
                placeholder="e.g. Python"
                aria-label="Required skill name"
                value={skillName}
                onChange={(e) => setSkillName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addSkill()
                  }
                }}
              />
              <select className="input select team-skill-cat" aria-label="Skill category" value={skillCategory} onChange={(e) => setSkillCategory(e.target.value)}>
                {SKILL_CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
              <Button type="button" size="sm" variant="secondary" onClick={addSkill}>
                <Plus size={14} /> Add
              </Button>
            </div>
            {form.required_skills.length > 0 && (
              <div className="team-skill-chips">
                {form.required_skills.map((s) => (
                  <span key={s.name.toLowerCase()} className="team-skill-chip">
                    {s.name} <Badge variant="neutral">{s.category}</Badge>
                    <button
                      type="button"
                      className="team-skill-remove"
                      onClick={() => setForm((f) => ({
                        ...f,
                        required_skills: f.required_skills.filter(
                          (x) => x.name.toLowerCase() !== s.name.toLowerCase()
                        ),
                      }))}
                    >
                      <Trash2 size={13} />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </Card>

          <Card className="review-card">
            <div className="review-section-header">
              <h3 className="review-section-title">Team settings</h3>
            </div>
            <div className="review-form">
              <Input
                label="Max team size (including you)"
                type="number"
                min={2}
                max={50}
                value={form.max_members}
                onChange={set('max_members')}
                required
              />
              <div className="review-form-row">
                <Input label="Location (optional)" value={form.location} onChange={set('location')} placeholder="e.g. Chennai or Remote" maxLength={120} />
                <Select label="Work mode" value={form.work_mode} onChange={set('work_mode')}>
                  <option value="">Select mode</option>
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="onsite">On-site</option>
                </Select>
              </div>
              <Select label="Category" value={form.category} onChange={set('category')}>
                <option value="">Select category</option>
                {PROJECT_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </Select>
              <CollegeSelect
                label="College (optional)"
                value={form.college ? { college_id: form.college_id, college: form.college } : null}
                onChange={(v) => setForm((f) => ({ ...f, college: v?.college || '', college_id: v?.college_id || null }))}
                hint="Required only when same-college is enabled"
              />
              <label className="toggle-row">
                <input type="checkbox" checked={form.require_same_college} onChange={set('require_same_college')} />
                <span className="toggle-label">
                  <span className="toggle-title">Require teammates from the same college</span>
                  <span className="toggle-desc">Only developers from the college above can join</span>
                </span>
              </label>
            </div>
          </Card>
        </div>

        <div className="review-footer">
          <Button type="button" variant="ghost" disabled={saving} onClick={() => navigate(isEdit ? `/teams/${id}` : '/teams')}>
            Cancel
          </Button>
          <Button type="submit" loading={saving}>
            {isEdit ? 'Save changes' : 'Create team'}
          </Button>
        </div>
      </form>
    </div>
  )
}
