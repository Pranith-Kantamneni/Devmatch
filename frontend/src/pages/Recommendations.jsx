import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { RefreshCw, Users, MapPin, Sparkles, ChevronRight, UserCheck } from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Avatar from '../components/ui/Avatar'
import EmptyState from '../components/ui/EmptyState'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'

function scoreColor(score) {
  if (score >= 0.7) return 'var(--success)'
  if (score >= 0.4) return 'var(--accent)'
  return 'var(--text-faint)'
}

function MatchScore({ score }) {
  const pct = Math.round(score * 100)
  return (
    <div className="match-score">
      <svg width="52" height="52" viewBox="0 0 52 52">
        <circle cx="26" cy="26" r="22" fill="none" stroke="var(--border)" strokeWidth="4" />
        <circle
          cx="26" cy="26" r="22" fill="none"
          stroke={scoreColor(score)} strokeWidth="4" strokeLinecap="round"
          strokeDasharray={`${(score * 138.2).toFixed(1)} 138.2`}
          transform="rotate(-90 26 26)"
          className="match-score-ring"
        />
      </svg>
      <span className="match-score-value" style={{ color: scoreColor(score) }}>{pct}%</span>
    </div>
  )
}

function TeammateCard({ rec }) {
  const { user, profile, similarity_score, skill_overlap } = rec
  const overlapSet = new Set((skill_overlap || []).map((s) => s.toLowerCase()))
  const freshSkills = (profile.skills || [])
    .map((s) => s.name)
    .filter((n) => !overlapSet.has(n.toLowerCase()))
  return (
    <Link to={`/developers/${user.id}`} className="dev-card">
      <div className="dev-card-top">
        <Avatar name={profile.full_name || user.username} size={52} />
        <div className="dev-card-id">
          <h3 className="dev-card-name">{profile.full_name || user.username}</h3>
          <p className="dev-card-username">@{user.username}</p>
        </div>
        <MatchScore score={similarity_score} />
      </div>

      {profile.bio && <p className="dev-card-bio">{profile.bio}</p>}

      <div className="dev-card-meta">
        {profile.availability && (
          <span className="dev-card-meta-item available"><UserCheck size={13} /> Open to teams</span>
        )}
        {profile.location && (
          <span className="dev-card-meta-item"><MapPin size={13} /> {profile.location}</span>
        )}
        {profile.experience_level && (
          <span className="dev-card-meta-item"><Sparkles size={13} /> {profile.experience_level}</span>
        )}
      </div>

      {profile.skills.length > 0 && (
        <div className="dev-card-skills">
          {profile.skills.slice(0, 5).map((s) => (
            <Badge key={s.skill_id} variant={skill_overlap.includes(s.name) ? 'accent' : 'neutral'}>
              {s.name}
            </Badge>
          ))}
          {profile.skills.length > 5 && (
            <Badge variant="neutral">+{profile.skills.length - 5}</Badge>
          )}
        </div>
      )}

      {skill_overlap.length > 0 && (
        <div className="dev-card-overlap">
          <span className="dev-card-overlap-label">You share:</span>
          {skill_overlap.slice(0, 3).map((s) => (
            <span key={s} className="dev-card-overlap-skill">{s}</span>
          ))}
        </div>
      )}
      {freshSkills.length > 0 && (
        <div className="dev-card-overlap dev-card-brings">
          <span className="dev-card-overlap-label">They bring:</span>
          {freshSkills.slice(0, 3).map((s) => (
            <span key={s} className="dev-card-overlap-skill">{s}</span>
          ))}
          {freshSkills.length > 3 && (
            <span className="dev-card-overlap-skill">+{freshSkills.length - 3}</span>
          )}
        </div>
      )}

      <div className="dev-card-cta">
        View teammate <ChevronRight size={15} />
      </div>
    </Link>
  )
}

export default function Recommendations() {
  const { toast } = useToast()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    setLoadError('')
    try {
      const res = await api.getRecommendations({ limit: 20 })
      setData(res)
    } catch (err) {
      setLoadError(err.message || 'Could not load recommendations')
      toast(err.message, 'error')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [toast])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-header-text">
          <h1 className="page-title">Find teammates</h1>
          <p className="page-subtitle">
            Developers ranked by how well their skills complement yours
          </p>
        </div>
        <Button variant="secondary" onClick={() => load(true)} loading={refreshing}>
          <RefreshCw size={15} /> Refresh
        </Button>
      </div>

      {loading ? (
        <div className="dev-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="dev-card skeleton-card">
              <div className="skeleton" style={{ width: '60%', height: 20, marginBottom: 12 }} />
              <div className="skeleton" style={{ width: '90%', height: 14, marginBottom: 8 }} />
              <div className="skeleton" style={{ width: '100%', height: 14, marginBottom: 8 }} />
              <div className="skeleton" style={{ width: '80%', height: 14 }} />
            </div>
          ))}
        </div>
      ) : loadError && !data ? (
        <Card>
          <EmptyState
            icon={<Users size={32} />}
            title="Could not load teammates"
            description={loadError}
            action={<Button size="sm" variant="secondary" onClick={() => load()}>Retry</Button>}
          />
        </Card>
      ) : !data || data.recommendations.length === 0 ? (
        <Card>
          <EmptyState
            icon={<Users size={32} />}
            title="No teammates found yet"
            description="Add skills and projects to your profile so the engine has something to match — or check back once more developers join."
            action={<Link to="/dashboard"><Button size="sm">Complete my profile</Button></Link>}
          />
        </Card>
      ) : (
        <>
          <div className="recs-meta">
            <span className="recs-meta-text">
              <strong>{data.recommendations.length}</strong> of <strong>{data.total_candidates}</strong> developers shown
            </span>
          </div>
          <div className="dev-grid">
            {data.recommendations.map((rec) => (
              <TeammateCard key={rec.user.id} rec={rec} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
