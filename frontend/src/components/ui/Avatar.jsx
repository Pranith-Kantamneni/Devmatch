const PALETTE = [
  '#0e7a55', '#1d5fa8', '#8a5a18', '#a03d2d',
  '#5b54a6', '#0f766e', '#7c3f67', '#4d6b2f',
  '#8a4b1f', '#3e5c76',
]

function colorFor(name = '') {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = (hash * 31 + name.charCodeAt(i)) >>> 0
  }
  return PALETTE[hash % PALETTE.length]
}

function initials(name = '') {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export default function Avatar({ name = '', size = 40, className = '' }) {
  const bg = colorFor(name)
  return (
    <div
      className={`avatar ${className}`}
      style={{
        width: size,
        height: size,
        background: bg,
        fontSize: size * 0.36,
      }}
    >
      {initials(name)}
    </div>
  )
}
