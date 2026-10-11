import { useEffect, useRef, useState } from 'react'
import { GraduationCap, X } from 'lucide-react'
import { api } from '../api/client'

/**
 * Searchable college picker backed by the canonical directory.
 * Value: { college_id: string|null, college: string } | null.
 * Typing free text offers a "Use custom" row so unlisted colleges work.
 */
export default function CollegeSelect({ label = 'College', value, onChange, placeholder = 'Search your college…', hint }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [results, setResults] = useState([])
  const [highlight, setHighlight] = useState(0)
  const [focused, setFocused] = useState(false)
  const timer = useRef(null)
  const boxRef = useRef(null)

  const selectedName = value?.college || ''

  useEffect(() => {
    if (!focused) return
    clearTimeout(timer.current)
    timer.current = setTimeout(async () => {
      try {
        const data = await api.listColleges(query.trim() ? { q: query.trim() } : {})
        setResults(data.colleges || [])
        setHighlight(0)
      } catch {
        setResults([])
      }
    }, 200)
    return () => clearTimeout(timer.current)
  }, [query, focused])

  useEffect(() => {
    const onDocClick = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDocClick)
    return () => document.removeEventListener('mousedown', onDocClick)
  }, [])

  const pick = (college_id, college) => {
    onChange(college ? { college_id, college } : null)
    setQuery('')
    setOpen(false)
  }

  const showCustom =
    query.trim() &&
    !results.some((r) => r.name.toLowerCase() === query.trim().toLowerCase())

  const flatCount = results.length + (showCustom ? 1 : 0)

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlight((h) => Math.min(h + 1, Math.max(flatCount - 1, 0)))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlight((h) => Math.max(h - 1, 0))
    } else if (e.key === 'Enter' && open && flatCount > 0) {
      e.preventDefault()
      if (highlight < results.length) {
        const r = results[highlight]
        pick(r.id, r.name)
      } else if (showCustom) {
        pick(null, query.trim())
      }
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="field" ref={boxRef}>
      {label && <label className="field-label">{label}</label>}
      {selectedName ? (
        <div className="combo-selected">
          <GraduationCap size={15} className="combo-selected-icon" />
          <span className="combo-selected-name">{selectedName}</span>
          {value?.college_id && <span className="combo-verified">Verified</span>}
          <button
            type="button"
            className="icon-btn"
            aria-label="Clear college"
            title="Clear college"
            onClick={() => pick(null, '')}
          >
            <X size={14} />
          </button>
        </div>
      ) : (
        <div className="combo-wrap">
          <input
            className="input"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setOpen(true)
            }}
            onFocus={() => {
              setFocused(true)
              setOpen(true)
            }}
            onBlur={() => setFocused(false)}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            role="combobox"
            aria-expanded={open}
            aria-label={label}
            autoComplete="off"
          />
          {open && (
            <ul className="combo-list" role="listbox">
              {results.map((r, i) => (
                <li key={r.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={i === highlight}
                    className={`combo-item ${i === highlight ? 'active' : ''}`}
                    onMouseDown={(e) => {
                      e.preventDefault()
                      pick(r.id, r.name)
                    }}
                    onMouseEnter={() => setHighlight(i)}
                  >
                    <span className="combo-item-main">
                      <span className="combo-item-name">{r.short}</span>
                      <span className="combo-item-sub">{r.name}</span>
                    </span>
                    <span className="combo-item-meta">{r.city}</span>
                  </button>
                </li>
              ))}
              {showCustom && (
                <li>
                  <button
                    type="button"
                    className={`combo-item combo-custom ${highlight === results.length ? 'active' : ''}`}
                    onMouseDown={(e) => {
                      e.preventDefault()
                      pick(null, query.trim())
                    }}
                    onMouseEnter={() => setHighlight(results.length)}
                  >
                    Use “{query.trim()}” (not listed)
                  </button>
                </li>
              )}
              {results.length === 0 && !showCustom && (
                <li className="combo-empty">Type at least 2 letters to search 360+ colleges</li>
              )}
            </ul>
          )}
        </div>
      )}
      {hint && <p className="field-hint">{hint}</p>}
    </div>
  )
}
