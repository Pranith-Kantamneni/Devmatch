import { Star } from 'lucide-react'

export default function Stars({ value, size = 14 }) {
  const stars = Math.max(1, Math.min(5, Math.round(value)))
  return (
    <span className="stars" title={`${stars} out of 5 stars`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <Star
          key={n}
          size={size}
          className={n <= stars ? 'star filled' : 'star'}
        />
      ))}
    </span>
  )
}
