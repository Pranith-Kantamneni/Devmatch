import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  Save, X, Plus, Trash2, User, Code2, Briefcase, GraduationCap,
  FolderKanban, FileText, Info,
} from 'lucide-react'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Textarea from '../components/ui/Textarea'
import Select from '../components/ui/Select'
import Button from '../components/ui/Button'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'

const SKILL_CATEGORIES = [
  { value: 'language', label: 'Language' },
  { value: 'framework', label: 'Framework' },
  { value: 'tool', label: 'Tool' },
  { value: 'domain', label: 'Domain' },
  { value: 'other', label: 'Other' },
]

const EXPERIENCE_LEVELS = [
  { value: 'student', label: 'Student' },
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid-level' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead' },
]

const EMPTY_SKILL = { name: '', category: 'language', proficiency: 3, years_experience: 1 }
const EMPTY_EXP = { title: '', company: '', duration: '', description: '' }
const EMPTY_EDU = { degree: '', institution: '', year: '' }
const EMPTY_PROJ = { title: '', description: '', skills: [], skillsText: '', url: '' }

function normalizeProject(p) {
  const skills = Array.isArray(p.skills) ? p.skills : []
  return {
    title: p.title || '',
    description: p.description || '',
    skills,
    skillsText: skills.join(', '),
    url: p.url || '',
  }
}

const STORAGE_KEY = 'devmatch_resume_parsed'

function loadStoredParsed() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export default function ResumeReview() {
  const location = useLocation()
  const navigate = useNavigate()
  const { toast } = useToast()

  const parsed = location.state?.parsed || loadStoredParsed()

  const [form, setForm] = useState(() => ({
    full_name: parsed?.full_name || '',
    email: parsed?.email || '',
    phone: parsed?.phone || '',
    location: parsed?.location || '',
    summary: parsed?.summary || '',
    experience_level: '',
    skills: parsed?.skills?.length ? parsed.skills.map((s) => ({ ...s })) : [{ ...EMPTY_SKILL }],
    experience: parsed?.experience?.length ? parsed.experience.map((e) => ({ ...e })) : [],
    education: parsed?.education?.length ? parsed.education.map((e) => ({ ...e })) : [],
    projects: parsed?.projects?.length ? parsed.projects.map(normalizeProject) : [],
  }))
  const [saving, setSaving] = useState(false)

  // Persist across refresh so a reload doesn't wipe the parsed data.
  useEffect(() => {
    if (location.state?.parsed) {
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(location.state.parsed))
      } catch {
        /* storage full/blocked — non-fatal */
      }
    }
  }, [location.state])

  const clearStored = () => {
    try {
      sessionStorage.removeItem(STORAGE_KEY)
    } catch {
      /* ignore */
    }
  }

  if (!parsed) {
    return (
      <div className="page">
        <Card>
          <div className="empty-state">
            <FileText size={32} />
            <h3 className="empty-title">No resume data</h3>
            <p className="empty-desc">Upload a resume first, then review the extracted details here.</p>
            <div className="empty-action">
              <Button variant="secondary" onClick={() => navigate('/dashboard')}>Go to dashboard</Button>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  const setField = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  const setSkill = (index, key, value) =>
    setForm((f) => ({
      ...f,
      skills: f.skills.map((s, i) => (i === index ? { ...s, [key]: value } : s)),
    }))

  const setExp = (index, key, value) =>
    setForm((f) => ({
      ...f,
      experience: f.experience.map((e, i) => (i === index ? { ...e, [key]: value } : e)),
    }))

  const setEdu = (index, key, value) =>
    setForm((f) => ({
      ...f,
      education: f.education.map((e, i) => (i === index ? { ...e, [key]: value } : e)),
    }))

  const setProj = (index, key, value) =>
    setForm((f) => ({
      ...f,
      projects: f.projects.map((p, i) => (i === index ? { ...p, [key]: value } : p)),
    }))

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.updateProfile({
        full_name: form.full_name || null,
        bio: form.summary || null,
        location: form.location || null,
        education: form.education?.[0]?.degree || null,
        experience_level: form.experience_level || null,
      })

      for (const skill of form.skills) {
        if (!skill.name.trim()) continue
        try {
          await api.addSkill({
            name: skill.name,
            category: skill.category,
            proficiency: skill.proficiency,
            years_experience: skill.years_experience,
          })
        } catch (err) {
          if (err.status !== 409) throw err
        }
      }

      for (const project of form.projects) {
        if (!project.title.trim()) continue
        const skill_names = (project.skillsText || '')
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean)
        await api.addProject({
          title: project.title,
          description: project.description || null,
          url: project.url.trim() || null,
          skill_names,
        })
      }

      toast('Profile updated from resume')
      clearStored()
      navigate('/dashboard', { replace: true })
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page">
      <div className="review-header">
        <div>
          <h1 className="page-title">Review extracted resume</h1>
          <p className="page-subtitle">Confirm and edit the details parsed from your resume</p>
        </div>
        <Button variant="ghost" onClick={() => { clearStored(); navigate('/dashboard', { replace: true }) }} disabled={saving}>
          <X size={16} /> Discard
        </Button>
      </div>

      {parsed.note && (
        <div className="review-note">
          <Info size={18} />
          <p>{parsed.note}</p>
        </div>
      )}

      <div className="review-grid">
        <Card className="review-card">
          <div className="review-section-header">
            <User size={18} className="review-section-icon" />
            <h3 className="review-section-title">Personal information</h3>
          </div>
          <div className="review-form">
            <Input label="Full name" value={form.full_name} onChange={(e) => setField('full_name', e.target.value)} placeholder="Your name" />
            <div className="review-form-row">
              <Input label="Email" value={form.email} onChange={(e) => setField('email', e.target.value)} placeholder="you@example.com" />
              <Input label="Phone" value={form.phone} onChange={(e) => setField('phone', e.target.value)} placeholder="(555) 123-4567" />
            </div>
            <Input label="Location" value={form.location} onChange={(e) => setField('location', e.target.value)} placeholder="City, Country" />
            <Select label="Experience level" value={form.experience_level} onChange={(e) => setField('experience_level', e.target.value)}>
              <option value="">Select level</option>
              {EXPERIENCE_LEVELS.map((l) => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </Select>
            <Textarea label="Summary" value={form.summary} onChange={(e) => setField('summary', e.target.value)} placeholder="Tell developers what you work on and care about" />
          </div>
        </Card>

        <Card className="review-card">
          <div className="review-section-header">
            <Code2 size={18} className="review-section-icon" />
            <h3 className="review-section-title">Skills</h3>
            <span className="section-count">{form.skills.length}</span>
            <Button size="sm" variant="ghost" onClick={() => setForm((f) => ({ ...f, skills: [...f.skills, { ...EMPTY_SKILL }] }))}>
              <Plus size={14} /> Add
            </Button>
          </div>
          <div className="review-note review-note-inline">
            <Info size={15} />
            <p>Default skill level is 3 and experience is 1. Change if required.</p>
          </div>
          <div className="review-list">
            {form.skills.map((skill, i) => (
              <div key={i} className="review-item">
                <div className="review-item-row">
                  <input
                    className="input review-skill-name"
                    placeholder="Skill name"
                    value={skill.name}
                    onChange={(e) => setSkill(i, 'name', e.target.value)}
                  />
                  <select
                    className="input select review-skill-cat"
                    value={skill.category}
                    onChange={(e) => setSkill(i, 'category', e.target.value)}
                  >
                    {SKILL_CATEGORIES.map((c) => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>
                <div className="review-item-row">
                  <div className="review-range">
                    <label>Level</label>
                    <input type="range" min="1" max="5" value={skill.proficiency} onChange={(e) => setSkill(i, 'proficiency', parseInt(e.target.value))} />
                    <span className="review-range-val">{skill.proficiency}/5</span>
                  </div>
                  <div className="review-years">
                    <label>Years</label>
                    <input type="number" min="0" step="0.5" className="input" value={skill.years_experience} onChange={(e) => setSkill(i, 'years_experience', parseFloat(e.target.value) || 0)} />
                  </div>
                  <button className="icon-btn danger review-remove" onClick={() => setForm((f) => ({ ...f, skills: f.skills.filter((_, idx) => idx !== i) }))} title="Remove">
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="review-card">
          <div className="review-section-header">
            <Briefcase size={18} className="review-section-icon" />
            <h3 className="review-section-title">Experience</h3>
            <Button size="sm" variant="ghost" onClick={() => setForm((f) => ({ ...f, experience: [...f.experience, { ...EMPTY_EXP }] }))}>
              <Plus size={14} /> Add
            </Button>
          </div>
          <div className="review-note review-note-inline">
            <Info size={15} />
            <p>Experience is kept for your reference — only profile fields, skills, and projects are saved.</p>
          </div>
          <div className="review-list">
            {form.experience.length === 0 && <p className="section-empty">No experience detected</p>}
            {form.experience.map((exp, i) => (
              <div key={i} className="review-item">
                <div className="review-item-row">
                  <input className="input" placeholder="Job title" value={exp.title || ''} onChange={(e) => setExp(i, 'title', e.target.value)} />
                  <input className="input" placeholder="Company" value={exp.company || ''} onChange={(e) => setExp(i, 'company', e.target.value)} />
                </div>
                <div className="review-item-row">
                  <input className="input" placeholder="Duration (e.g. 2021 - Present)" value={exp.duration || ''} onChange={(e) => setExp(i, 'duration', e.target.value)} />
                  <button className="icon-btn danger review-remove" onClick={() => setForm((f) => ({ ...f, experience: f.experience.filter((_, idx) => idx !== i) }))} title="Remove">
                    <Trash2 size={15} />
                  </button>
                </div>
                <textarea className="input textarea" placeholder="Description" value={exp.description || ''} onChange={(e) => setExp(i, 'description', e.target.value)} />
              </div>
            ))}
          </div>
        </Card>

        <Card className="review-card">
          <div className="review-section-header">
            <GraduationCap size={18} className="review-section-icon" />
            <h3 className="review-section-title">Education</h3>
            <Button size="sm" variant="ghost" onClick={() => setForm((f) => ({ ...f, education: [...f.education, { ...EMPTY_EDU }] }))}>
              <Plus size={14} /> Add
            </Button>
          </div>
          <div className="review-list">
            {form.education.length === 0 && <p className="section-empty">No education detected</p>}
            {form.education.map((edu, i) => (
              <div key={i} className="review-item">
                <div className="review-item-row">
                  <input className="input" placeholder="Degree" value={edu.degree || ''} onChange={(e) => setEdu(i, 'degree', e.target.value)} />
                  <input className="input" placeholder="Institution" value={edu.institution || ''} onChange={(e) => setEdu(i, 'institution', e.target.value)} />
                </div>
                <div className="review-item-row">
                  <input className="input" placeholder="Year (e.g. 2020)" value={edu.year || ''} onChange={(e) => setEdu(i, 'year', e.target.value)} />
                  <button className="icon-btn danger review-remove" onClick={() => setForm((f) => ({ ...f, education: f.education.filter((_, idx) => idx !== i) }))} title="Remove">
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="review-card">
          <div className="review-section-header">
            <FolderKanban size={18} className="review-section-icon" />
            <h3 className="review-section-title">Projects</h3>
            <Button size="sm" variant="ghost" onClick={() => setForm((f) => ({ ...f, projects: [...f.projects, { ...EMPTY_PROJ }] }))}>
              <Plus size={14} /> Add
            </Button>
          </div>
          <div className="review-list">
            {form.projects.length === 0 && <p className="section-empty">No projects detected</p>}
            {form.projects.map((proj, i) => (
              <div key={i} className="review-item">
                <div className="review-item-row">
                  <input className="input" placeholder="Project title" aria-label="Project title" value={proj.title || ''} onChange={(e) => setProj(i, 'title', e.target.value)} />
                  <button className="icon-btn danger review-remove" onClick={() => setForm((f) => ({ ...f, projects: f.projects.filter((_, idx) => idx !== i) }))} title="Remove project" aria-label="Remove project">
                    <Trash2 size={15} />
                  </button>
                </div>
                <textarea className="input textarea" placeholder="Description" aria-label="Project description" value={proj.description || ''} onChange={(e) => setProj(i, 'description', e.target.value)} />
                <div className="review-item-row">
                  <input className="input" placeholder="Tech used (comma separated)" aria-label="Technologies used" value={proj.skillsText || ''} onChange={(e) => setProj(i, 'skillsText', e.target.value)} />
                  <input className="input" placeholder="Link (https://…)" aria-label="Project link" value={proj.url || ''} onChange={(e) => setProj(i, 'url', e.target.value)} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="review-footer">
        <Button variant="ghost" onClick={() => { clearStored(); navigate('/dashboard', { replace: true }) }} disabled={saving}>Discard</Button>
        <Button onClick={handleSave} loading={saving}>
          <Save size={16} /> Save to profile
        </Button>
      </div>
    </div>
  )
}
