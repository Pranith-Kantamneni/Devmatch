import { Check, Circle, ListChecks } from 'lucide-react'
import Card from './ui/Card'

/**
 * Guides new users to a discoverable profile. Purely derived from the
 * loaded profile — hides itself once everything is done.
 */
export default function OnboardingChecklist({ profile, actions }) {
  const steps = [
    {
      key: 'name',
      label: 'Add your name',
      done: !!(profile.full_name && profile.full_name.trim()),
      action: actions.onEdit,
      actionLabel: 'Edit',
    },
    {
      key: 'bio',
      label: 'Write a short bio',
      done: !!(profile.bio && profile.bio.trim()),
      action: actions.onEdit,
      actionLabel: 'Edit',
    },
    {
      key: 'level',
      label: 'Set experience level',
      done: !!profile.experience_level,
      action: actions.onEdit,
      actionLabel: 'Edit',
    },
    {
      key: 'college',
      label: 'Select your college',
      done: !!(profile.college && profile.college.trim()),
      action: actions.onEdit,
      actionLabel: 'Edit',
    },
    {
      key: 'skills',
      label: 'Add at least 1 skill',
      done: (profile.skills || []).length > 0,
      action: actions.onAddSkill,
      actionLabel: 'Add',
    },
    {
      key: 'projects',
      label: 'Showcase 1 project',
      done: (profile.projects || []).length > 0,
      action: actions.onAddProject,
      actionLabel: 'Add',
    },
    {
      key: 'available',
      label: 'Mark yourself available',
      done: !!profile.availability,
      action: actions.onEdit,
      actionLabel: 'Edit',
    },
  ]

  const doneCount = steps.filter((s) => s.done).length
  if (doneCount === steps.length) return null

  return (
    <Card className="side-card onboarding-card">
      <div className="side-card-header">
        <ListChecks size={18} className="side-icon" />
        <h3 className="side-title">Get discovered</h3>
        <span className="section-count">{doneCount}/{steps.length}</span>
      </div>
      <div className="readiness-bar" aria-hidden="true">
        <div
          className="readiness-fill"
          style={{ width: `${Math.round((doneCount / steps.length) * 100)}%` }}
        />
      </div>
      <ul className="onboarding-list">
        {steps.map((step) => (
          <li key={step.key} className={`onboarding-step ${step.done ? 'done' : ''}`}>
            <span className="onboarding-check">
              {step.done ? <Check size={13} /> : <Circle size={13} />}
            </span>
            <span className="onboarding-label">{step.label}</span>
            {!step.done && (
              <button className="onboarding-action" onClick={step.action}>
                {step.actionLabel}
              </button>
            )}
          </li>
        ))}
      </ul>
    </Card>
  )
}
