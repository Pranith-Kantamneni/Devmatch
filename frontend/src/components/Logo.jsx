export default function Logo({ size = 30 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#1b1a17" />
      <path
        d="M9 23V9l7 8 7-8v12"
        stroke="#f4f2ec"
        strokeWidth="2.6"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="16" cy="17" r="3.4" fill="#2fa37c" />
      <circle cx="16" cy="17" r="1.3" fill="#f4f2ec" />
    </svg>
  )
}
