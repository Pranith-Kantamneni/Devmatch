export default function Select({ label, error, hint, className = '', id, children, ...props }) {
  const inputId = id || props.name
  return (
    <div className={`field ${className}`}>
      {label && <label className="field-label" htmlFor={inputId}>{label}</label>}
      <select className={`input select ${error ? 'input-error' : ''}`} id={inputId} {...props}>
        {children}
      </select>
      {error && <p className="field-error">{error}</p>}
      {hint && !error && <p className="field-hint">{hint}</p>}
    </div>
  )
}
