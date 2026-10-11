import { useEffect, useState } from 'react'
import { Puzzle, Search, Check } from 'lucide-react'
import Card from './ui/Card'
import Badge from './ui/Badge'
import Button from './ui/Button'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'

/**
 * The creator's hiring checklist: which required skills the current roster
 * covers, what's still missing, and one-tap search for each gap.
 */
export default function TeamGapsPanel({ projectId, onFindSkill }) {
  const { toast } = useToast()
  const [gaps, setGaps] = useState(null)

  useEffect(() => {
    let cancelled = false
    api
      .getTeamSkillGaps(projectId)
      .then((g) => {
        if (!cancelled) setGaps(g)
      })
      .catch((err) => {
        if (!cancelled) toast(err.message, 'error')
      })
    return () => {
      cancelled = true
    }
  }, [projectId, toast])

  if (!gaps || gaps.total_required === 0) return null

  const pct = Math.round((gaps.coverage || 0) * 100)

  return (
    <Card className="section-card gaps-panel">
      <div className="section-header">
        <div className="section-title-wrap">
          <Puzzle size={18} className="section-icon" />
          <h3 className="section-title">Team skill gaps</h3>
          <Badge variant={pct === 100 ? 'success' : 'accent'}>
            {pct}% covered
          </Badge>
        </div>
      </div>

      <div className="readiness-bar" aria-hidden="true">
        <div className="readiness-fill" style={{ width: `${pct}%` }} />
      </div>

      {gaps.uncovered_skills.length > 0 ? (
        <>
          <p className="gaps-label">Still needed — find someone who brings:</p>
          <div className="gaps-chips">
            {gaps.uncovered_skills.map((skill) => (
              <span key={skill} className="gap-chip">
                {skill}
                <button
                  className="gap-find"
                  onClick={() => onFindSkill(skill)}
                  title={`Find developers who know ${skill}`}
                >
                  <Search size={12} /> Find
                </button>
              </span>
            ))}
          </div>
        </>
      ) : (
        <p className="gaps-complete">
          <Check size={14} /> Every required skill is covered by your roster.
        </p>
      )}

      {gaps.covered_skills.length > 0 && (
        <div className="gaps-covered">
          <span className="gaps-covered-label">Covered:</span>
          {gaps.by_skill
            .filter((s) => s.covered_by_members > 0)
            .map((s) => (
              <Badge key={s.skill} variant="neutral">
                {s.skill} ×{s.covered_by_members}
              </Badge>
            ))}
        </div>
      )}
    </Card>
  )
}
