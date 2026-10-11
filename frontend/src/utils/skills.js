/**
 * Mirrors backend `canonical_skill_name` (matching_service.py): lowercase,
 * strip separators, resolve aliases — so "Fast Api", "fast_api" and
 * "FastAPI" compare equal everywhere in the UI.
 */

const ALIASES = {
  js: 'javascript',
  ts: 'typescript',
  reactjs: 'react',
  'react.js': 'react',
  nodejs: 'node.js',
  node: 'node.js',
  nextjs: 'next.js',
  vuejs: 'vue',
  'vue.js': 'vue',
  postgres: 'postgresql',
  psql: 'postgresql',
  mongo: 'mongodb',
  ml: 'machine learning',
  ai: 'artificial intelligence',
  nlp: 'natural language processing',
  cpp: 'c++',
  cplusplus: 'c++',
  csharp: 'c#',
  'c-sharp': 'c#',
  sklearn: 'scikit-learn',
  'scikit learn': 'scikit-learn',
  torch: 'pytorch',
  k8s: 'kubernetes',
  gcp: 'google cloud',
  tf: 'tensorflow',
  tailwindcss: 'tailwind',
  'tailwind css': 'tailwind',
}

const squash = (s) => (s || '').trim().toLowerCase().replace(/[\s_.\-]+/g, '')

const SQUASHED_ALIASES = Object.fromEntries(
  Object.entries(ALIASES).map(([k, v]) => [squash(k), v])
)

export function canonicalSkill(name) {
  const key = squash(name)
  return SQUASHED_ALIASES[key] || key
}

export function sameSkill(a, b) {
  return canonicalSkill(a) === canonicalSkill(b)
}
