import { Link, Navigate } from 'react-router-dom'
import {
  ArrowRight, Users, Code2, Zap, Target, Check, ShieldCheck, FileUp, Sparkles,
} from 'lucide-react'
import Logo from '../components/Logo'
import ThemeToggle from '../components/ThemeToggle'
import Button from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'

const FEATURES = [
  {
    icon: <Code2 size={20} />,
    title: 'Skill-based matching',
    desc: 'Your stack, projects, and experience are matched against every developer on the platform — ranked by fit, not follower counts.',
  },
  {
    icon: <Target size={20} />,
    title: 'Complementary, not identical',
    desc: 'DevMatch surfaces people who fill the gaps in your team: a frontend dev finds backend help, a designer finds an ML engineer.',
  },
  {
    icon: <Zap size={20} />,
    title: 'Built for hackathon pace',
    desc: 'Post a team with required skills, get star-rated recommendations, invite, and fill seats before the clock runs out.',
  },
]

const STEPS = [
  { step: '01', title: 'Build your profile', desc: 'Add skills, projects, and experience — or upload a resume and review the extracted details in seconds.' },
  { step: '02', title: 'Get matched', desc: 'The engine ranks developers by skill overlap, project fit, and experience compatibility.' },
  { step: '03', title: 'Form your team', desc: 'Create a team project, invite top matches, and manage applications in one place.' },
]

const ASSURANCES = ['Free to use', 'No credit card required', 'Set up in minutes']

export default function Landing() {
  const { isAuthenticated, loading } = useAuth()
  if (!loading && isAuthenticated) return <Navigate to="/home" replace />
  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="landing-nav-inner">
          <Link to="/" className="landing-brand">
            <Logo size={30} />
            <span className="brand-name">Dev<span className="brand-accent">Match</span></span>
          </Link>
          <div className="landing-nav-actions">
            <ThemeToggle />
            <Link to="/login" className="landing-login">Log in</Link>
            <Link to="/register">
              <Button size="sm">Get started <ArrowRight size={14} /></Button>
            </Link>
          </div>
        </div>
      </header>

      <section className="landing-hero">
        <div className="landing-hero-content">
          <p className="landing-eyebrow">Hackathon team formation</p>
          <h1 className="landing-headline">
            Find developers who <span className="landing-headline-accent">complete</span> your team
          </h1>
          <p className="landing-sub">
            DevMatch reads your skills, projects, and experience, then ranks the
            developers you’ll actually enjoy building with. Stop cold-messaging —
            start matching.
          </p>
          <div className="landing-cta">
            <Link to="/register">
              <Button size="lg">Find your teammates <ArrowRight size={17} /></Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="secondary">I have an account</Button>
            </Link>
          </div>

          <Link to="/register" className="hero-mock" aria-label="See an example match — get started">
            <div className="hero-mock-card">
              <div className="hero-mock-top">
                <span className="hero-mock-avatar">AK</span>
                <span className="hero-mock-id">
                  <span className="hero-mock-name">Ada K. · Backend</span>
                  <span className="hero-mock-sub">shares Python, FastAPI · adds Docker</span>
                </span>
                <span className="hero-mock-ring" aria-hidden="true">
                  <svg width="46" height="46" viewBox="0 0 52 52">
                    <circle cx="26" cy="26" r="22" fill="none" stroke="var(--border)" strokeWidth="5" />
                    <circle cx="26" cy="26" r="22" fill="none" stroke="var(--accent)" strokeWidth="5" strokeLinecap="round" strokeDasharray="127.3 138.2" transform="rotate(-90 26 26)" />
                  </svg>
                  <span className="hero-mock-pct">92%</span>
                </span>
              </div>
              <div className="hero-mock-skills">
                <span className="badge badge-accent">Python</span>
                <span className="badge badge-accent">FastAPI</span>
                <span className="badge badge-success">Docker</span>
              </div>
              <div className="hero-mock-foot">
                <span className="hero-mock-proof">Used FastAPI in 2 shipped projects</span>
                <span className="hero-mock-invite">Invite</span>
              </div>
            </div>
            <div className="hero-float hero-float-a">
              <Check size={14} /> Invite accepted — Karim joined AI Builders
            </div>
            <div className="hero-float hero-float-b">
              <Sparkles size={14} /> polls · chat · skill gaps built in
            </div>
          </Link>

          <div className="landing-assurance">
            {ASSURANCES.map((a) => (
              <span key={a} className="landing-assurance-item">
                <Check size={14} /> {a}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-section">
        <div className="landing-container">
          <span className="landing-section-eyebrow">How it works</span>
          <h2 className="landing-section-title">Three steps to a full roster</h2>
          <p className="landing-section-sub">From empty profile to matched team in one sitting</p>
          <div className="landing-steps">
            {STEPS.map((s) => (
              <div key={s.step} className="landing-step">
                <span className="landing-step-num">{s.step}</span>
                <h3 className="landing-step-title">{s.title}</h3>
                <p className="landing-step-desc">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-section landing-section-alt">
        <div className="landing-container">
          <span className="landing-section-eyebrow">Why DevMatch</span>
          <h2 className="landing-section-title">Matching with receipts</h2>
          <p className="landing-section-sub">Every recommendation shows its skill overlap and score</p>
          <div className="landing-features">
            {FEATURES.map((f) => (
              <div key={f.title} className="landing-feature">
                <div className="landing-feature-icon">{f.icon}</div>
                <h3 className="landing-feature-title">{f.title}</h3>
                <p className="landing-feature-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-section">
        <div className="landing-container">
          <span className="landing-section-eyebrow">Also included</span>
          <h2 className="landing-section-title">Everything a team needs</h2>
          <p className="landing-section-sub">Beyond matching</p>
          <div className="landing-features">
            <div className="landing-feature">
              <div className="landing-feature-icon"><FileUp size={20} /></div>
              <h3 className="landing-feature-title">Resume import</h3>
              <p className="landing-feature-desc">Upload a PDF, DOCX, or TXT resume — skills, experience, and projects are extracted for your review.</p>
            </div>
            <div className="landing-feature">
              <div className="landing-feature-icon"><Users size={20} /></div>
              <h3 className="landing-feature-title">Team workspaces</h3>
              <p className="landing-feature-desc">Required skills, tech stack, college rules, applications, and invites — managed per project.</p>
            </div>
            <div className="landing-feature">
              <div className="landing-feature-icon"><ShieldCheck size={20} /></div>
              <h3 className="landing-feature-title">Sign in your way</h3>
              <p className="landing-feature-desc">Password, Google, GitHub, or LinkedIn. Verified emails only, secured sessions throughout.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-cta-section">
        <div className="landing-cta-panel">
          <h2 className="landing-cta-title">Your next teammate is <em>already here</em></h2>
          <p className="landing-cta-sub">Create your profile and see your first matches in minutes.</p>
          <Link to="/register">
            <Button size="lg">Get started free <ArrowRight size={17} /></Button>
          </Link>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="landing-container landing-footer-inner">
          <div className="landing-brand">
            <Logo size={24} />
            <span className="brand-name">Dev<span className="brand-accent">Match</span></span>
          </div>
          <p className="landing-footer-text">Find developers who complement your skills.</p>
        </div>
      </footer>
    </div>
  )
}
