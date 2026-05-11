import { useState } from 'react'

export default function StarRating({ value = 0, onChange, disabled = false }) {
  const [hovered, setHovered] = useState(0)
  const active = hovered || value

  return (
    <div className="star-rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className={star <= active ? 'filled' : ''}
          onClick={() => !disabled && onChange?.(star)}
          onMouseEnter={() => !disabled && setHovered(star)}
          onMouseLeave={() => !disabled && setHovered(0)}
          disabled={disabled}
          title={`${star} star${star > 1 ? 's' : ''}`}
        >
          ★
        </button>
      ))}
    </div>
  )
}
