export default function Textarea({ label, error, hint, className = '', id, ...props }) {
  const inputId = id || props.name
  return (
    <div className={`field ${className}`}>
      {label && <label className="field-label" htmlFor={inputId}>{label}</label>}
      <textarea className={`input textarea ${error ? 'input-error' : ''}`} id={inputId} {...props} />
      {error && <p className="field-error">{error}</p>}
      {hint && !error && <p className="field-hint">{hint}</p>}
    </div>
  )
}
