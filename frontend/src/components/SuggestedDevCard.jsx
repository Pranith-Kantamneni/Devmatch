import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, FolderKanban } from 'lucide-react'
import Avatar from './ui/Avatar'
import Badge from './ui/Badge'
import Button from './ui/Button'
import Stars from './ui/Stars'

/**
 * A creator-facing match card answering:
 * what do you share, what do they add, what's still missing,
 * and proof they've used the required tech in real projects.
 */
export default function SuggestedDevCard({ rec, inviting, onInvite }) {
  const [expanded, setExpanded] = useState(false)
  const coverage = Math.round((rec.coverage || 0) * 100)
  const overlap = rec.skill_overlap || []
  const bonus = rec.bonus_skills || []
  const missing = rec.missing_skills || []
  const totalRequired = overlap.length + missing.length
  const evidence = (rec.skill_evidence || []).filter((e) => e.project_titles.length > 0)
  const provenCount = evidence.length

  return (
    <div className="match-card">
      <div className="match-card-top">
        <Avatar name={rec.full_name || rec.username} size={44} />
        <div className="match-card-id">
          <Link to={`/developers/${rec.user_id}`} className="suggest-name">
            {rec.full_name || rec.username}
          </Link>
          <span className="match-card-sub">
            <Stars value={rec.stars} size={13} />
            {totalRequired > 0 && (
              <span className="match-coverage-text">
                covers {overlap.length} of {totalRequired} skills
              </span>
            )}
          </span>
        </div>
        {rec.invitation_status === 'pending' ? (
          <Badge variant="accent">Invited</Badge>
        ) : rec.application_status === 'pending' ? (
          <Badge variant="neutral">Applied</Badge>
        ) : (
          <Button
            size="sm"
            variant="secondary"
            disabled={inviting}
            onClick={() => onInvite(rec.user_id)}
          >
            Invite
          </Button>
        )}
      </div>

      <div className="readiness-bar match-bar" aria-hidden="true">
        <div className="readiness-fill" style={{ width: `${coverage}%` }} />
      </div>

      {overlap.length > 0 && (
        <div className="match-row">
          <span className="match-label">You share</span>
          <span className="match-chips">
            {overlap.map((s) => (
              <Badge key={s} variant="accent">{s}</Badge>
            ))}
          </span>
        </div>
      )}

      {bonus.length > 0 && (
        <div className="match-row">
          <span className="match-label">They add</span>
          <span className="match-chips">
            {bonus.slice(0, 4).map((s) => (
              <Badge key={s} variant="success">{s}</Badge>
            ))}
            {bonus.length > 4 && (
              <span className="match-more">+{bonus.length - 4}</span>
            )}
          </span>
        </div>
      )}

      {missing.length > 0 && (
        <div className="match-row">
          <span className="match-label">Still missing</span>
          <span className="match-chips match-missing">
            {missing.slice(0, 4).map((s) => (
              <span key={s} className="match-missing-chip">{s}</span>
            ))}
            {missing.length > 4 && (
              <span className="match-more">+{missing.length - 4}</span>
            )}
          </span>
        </div>
      )}

      {provenCount > 0 && (
        <button
          className="match-proof-toggle"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
        >
          <FolderKanban size={14} />
          Project proof ({provenCount} skill{provenCount === 1 ? '' : 's'} used in real projects)
          <ChevronDown size={14} className={expanded ? 'flip' : ''} />
        </button>
      )}

      {expanded && (
        <ul className="match-proof-list">
          {evidence.map((e) => (
            <li key={e.skill} className="match-proof-item">
              <span className="match-proof-skill">{e.skill}</span>
              {e.listed && <Badge variant="neutral">listed</Badge>}
              <span className="match-proof-projects">
                {e.project_titles.join(' · ')}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
