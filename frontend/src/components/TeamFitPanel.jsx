import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Gauge, Check, Plus } from 'lucide-react'
import Card from './ui/Card'
import Badge from './ui/Badge'
import Button from './ui/Button'
import { api } from '../api/client'
import { canonicalSkill } from '../utils/skills'

/**
 * "Should I apply?" — compares the viewer's skills against what the team
 * asks for. Listed skills and project-tagged skills are matched with the
 * same canonicalization as the backend; project-sourced matches are marked
 * "via {project}" so nothing looks mysteriously shared.
 */
export default function TeamFitPanel({ project, onApply }) {
  const [mine, setMine] = useState(null)

  useEffect(() => {
    let cancelled = false
    api
      .getMyProfile()
      .then((p) => {
        if (!cancelled) setMine(p)
      })
      .catch(() => {
        if (!cancelled) setMine(null)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (!mine || project.is_creator || project.is_member) return null

  // norm -> { name, via: project title | null }
  const mySkills = new Map()
  for (const s of mine.skills || []) {
    if (!s.name) continue
    const key = canonicalSkill(s.name)
    if (!mySkills.has(key)) mySkills.set(key, { name: s.name, via: null })
  }
  for (const p of mine.projects || []) {
    for (const s of p.skills || []) {
      if (!s.name) continue
      const key = canonicalSkill(s.name)
      if (!mySkills.has(key)) {
        mySkills.set(key, { name: s.name, via: p.title || 'a project' })
      }
    }
  }

  const wanted = [
    ...(project.required_skills || []).map((s) => s.name),
    ...(project.tech_stack || []),
  ]
  const seen = new Set()
  const uniqueWanted = []
  for (const w of wanted) {
    const key = canonicalSkill(w)
    if (!key || seen.has(key)) continue
    seen.add(key)
    uniqueWanted.push({ key, name: w })
  }

  if (uniqueWanted.length === 0) return null

  const matched = uniqueWanted.filter((w) => mySkills.has(w.key))
  const missing = uniqueWanted.filter((w) => !mySkills.has(w.key))
  const pct = Math.round((matched.length / uniqueWanted.length) * 100)
  const verdict =
    pct >= 70 ? 'Strong fit' : pct >= 40 ? 'Good fit' : pct > 0 ? 'Stretch fit' : 'No overlap yet'

  return (
    <Card className="section-card fit-panel">
      <div className="section-header">
        <div className="section-title-wrap">
          <Gauge size={18} className="section-icon" />
          <h3 className="section-title">Your fit for this team</h3>
          <Badge variant={pct >= 40 ? 'success' : 'neutral'}>{verdict} · {pct}%</Badge>
        </div>
      </div>
      <div className="readiness-bar" aria-hidden="true">
        <div className="readiness-fill" style={{ width: `${pct}%` }} />
      </div>
      {matched.length > 0 && (
        <div className="fit-line fit-shared">
          <Check size={14} className="fit-check" />
          <span>
            You share{' '}
            {matched.slice(0, 4).map((w, i) => {
              const src = mySkills.get(w.key)
              return (
                <span key={w.key}>
                  {i > 0 && ', '}
                  <strong>{src.name}</strong>
                  {src.via && <span className="fit-via"> via {src.via}</span>}
                </span>
              )
            })}
            {matched.length > 4 && ` +${matched.length - 4} more`}
          </span>
        </div>
      )}
      {missing.length > 0 && (
        <p className="fit-line fit-missing">
          <Plus size={14} />
          <span>
            They also want {missing.slice(0, 4).map((w) => w.name).join(', ')}
            {missing.length > 4 && ` +${missing.length - 4} more`}
          </span>
        </p>
      )}
      <div className="fit-actions">
        <Button size="sm" onClick={onApply}>Apply to join</Button>
        {missing.length > 0 && (
          <Link to="/dashboard" className="fit-link">
            Add missing skills to your profile
          </Link>
        )}
      </div>
    </Card>
  )
}
