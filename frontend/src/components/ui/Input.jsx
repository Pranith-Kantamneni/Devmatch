import { useId } from 'react'

export default function Input({
  label,
  error,
  hint,
  className = '',
  id,
  ...props
}) {
  const autoId = useId()
  const inputId = id || props.name || autoId
  return (
    <div className={`field ${className}`}>
      {label && <label className="field-label" htmlFor={inputId}>{label}</label>}
      <input
        className={`input ${error ? 'input-error' : ''}`}
        id={inputId}
        aria-invalid={error ? true : undefined}
        {...props}
      />
      {error && <p className="field-error" role="alert">{error}</p>}
      {hint && !error && <p className="field-hint">{hint}</p>}
    </div>
  )
}
