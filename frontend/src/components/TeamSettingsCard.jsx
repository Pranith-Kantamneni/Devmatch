import { useState } from 'react'
import { Settings2 } from 'lucide-react'
import Card from './ui/Card'
import Button from './ui/Button'
import { api } from '../api/client'
import { useToast } from '../context/ToastContext'

/** Creator-only team permissions. Changes apply instantly. */
export default function TeamSettingsCard({ project, onSaved }) {
  const { toast } = useToast()
  const [allowPolls, setAllowPolls] = useState(!!project.allow_member_polls)
  const [allowInvites, setAllowInvites] = useState(!!project.allow_member_invites)
  const [saving, setSaving] = useState(false)

  const dirty =
    allowPolls !== !!project.allow_member_polls ||
    allowInvites !== !!project.allow_member_invites

  const save = async () => {
    setSaving(true)
    try {
      await api.updateTeamProject(project.id, {
        allow_member_polls: allowPolls,
        allow_member_invites: allowInvites,
      })
      toast('Team settings saved')
      onSaved()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="section-card">
      <div className="section-header">
        <div className="section-title-wrap">
          <Settings2 size={18} className="section-icon" />
          <h3 className="section-title">Team settings</h3>
        </div>
        {dirty && (
          <Button size="sm" loading={saving} onClick={save}>
            Save
          </Button>
        )}
      </div>
      <label className="toggle-row">
        <input
          type="checkbox"
          checked={allowPolls}
          onChange={(e) => setAllowPolls(e.target.checked)}
        />
        <span className="toggle-label">
          <span className="toggle-title">Teammates can create polls</span>
          <span className="toggle-desc">Off = only you can start votes</span>
        </span>
      </label>
      <label className="toggle-row" style={{ marginTop: 12 }}>
        <input
          type="checkbox"
          checked={allowInvites}
          onChange={(e) => setAllowInvites(e.target.checked)}
        />
        <span className="toggle-label">
          <span className="toggle-title">Teammates can invite developers</span>
          <span className="toggle-desc">Off = only you can send invites</span>
        </span>
      </label>
    </Card>
  )
}
