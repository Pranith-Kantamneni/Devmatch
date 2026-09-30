export default function Spinner({ size = 32, className = '' }) {
  return (
    <div className={`spinner-wrap ${className}`}>
      <div className="spinner" style={{ width: size, height: size }} />
    </div>
  )
}
