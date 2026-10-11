import { X } from 'lucide-react'
import { useEffect, useRef } from 'react'

export default function Modal({ open, onClose, title, children, footer }) {
  const dialogRef = useRef(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose
  const wasOpen = useRef(open)

  useEffect(() => {
    if (!open) {
      wasOpen.current = false
      return
    }
    const handleKey = (e) => {
      if (e.key === 'Escape') onCloseRef.current()
    }
    window.addEventListener('keydown', handleKey)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    // Move focus into the dialog exactly once per opening — never steal it
    // back on unrelated parent re-renders (polling, refreshes).
    if (!wasOpen.current) {
      wasOpen.current = true
      dialogRef.current?.querySelector('button, input, select, textarea, [tabindex]')?.focus?.()
    }
    return () => {
      window.removeEventListener('keydown', handleKey)
      document.body.style.overflow = prevOverflow
    }
  }, [open])

  if (!open) return null

  return (
    <div className="modal-overlay" onClick={() => onCloseRef.current()}>
      <div
        ref={dialogRef}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === 'string' ? title : 'Dialog'}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 className="modal-title">{title}</h2>
          <button className="modal-close" onClick={() => onCloseRef.current()} aria-label="Close dialog">
            <X size={18} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  )
}
