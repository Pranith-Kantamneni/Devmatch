import { Link } from 'react-router-dom'
import {
  ArrowRight, Users, Code2, Sparkles, Zap, Target, ShieldCheck, Github,
} from 'lucide-react'
import Logo from '../components/Logo'
import Button from '../components/ui/Button'

const FEATURES = [
  {
    icon: <Code2 size={20} />,
    title: 'Skill-based matching',
    desc: 'Your tech stack is converted into a vector and matched against other developers to find your ideal teammates.',
  },
  {
    icon: <Target size={20} />,
    title: 'Complementary teams',
    desc: 'Find developers whose skills fill the gaps in yours — not just people who stack the same tools.',
  },
  {
    icon: <Zap size={20} />,
    title: 'Hackathon-ready profiles',
    desc: 'Showcase your projects, experience, and availability so teams can find you fast.',
  },
]

const STEPS = [
  { step: '01', title: 'Build your profile', desc: 'Add your skills, projects, and what you\'re looking for in a team.' },
  { step: '02', title: 'Get matched', desc: 'Our engine ranks developers by how well they complement you.' },
  { step: '03', title: 'Form your team', desc: 'Connect with your top matches and start building together.' },
]

export default function Landing() {
  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="landing-nav-inner">
          <Link to="/" className="landing-brand">
            <Logo size={30} />
            <span className="brand-name">DevMatch</span>
          </Link>
          <div className="landing-nav-actions">
            <Link to="/login" className="landing-login">Log in</Link>
            <Link to="/register">
              <Button size="sm">Get started <ArrowRight size={14} /></Button>
            </Link>
          </div>
        </div>
      </header>

      <section className="landing-hero">
        <div className="landing-hero-glow" />
        <div className="landing-hero-content">
          <div className="landing-badge">
            <Sparkles size={14} />
            <span>Hackathon team formation</span>
          </div>
          <h1 className="landing-headline">
            Form your dream
            <span className="landing-headline-accent"> hackathon team</span>
          </h1>
          <p className="landing-sub">
            DevMatch analyzes your skills, projects, and experience to connect you
            with developers you'll actually enjoy building with. Stop searching,
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
          <div className="landing-proof">
            <div className="landing-proof-avatars">
              {['AK', 'JM', 'RS', 'TL'].map((i) => (
                <span key={i} className="landing-proof-avatar">{i}</span>
              ))}
            </div>
            <p className="landing-proof-text">Trusted by developers forming hackathon teams</p>
          </div>
        </div>
      </section>

      <section className="landing-section">
        <div className="landing-container">
          <h2 className="landing-section-title">How it works</h2>
          <p className="landing-section-sub">Three steps to your ideal hackathon team</p>
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
          <h2 className="landing-section-title">Why DevMatch</h2>
          <p className="landing-section-sub">Built for developers who want to build together</p>
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

      <section className="landing-cta-section">
        <div className="landing-container">
          <h2 className="landing-cta-title">Ready to find your team?</h2>
          <p className="landing-cta-sub">Create your profile and get your first matches in minutes.</p>
          <Link to="/register">
            <Button size="lg">Get started free <ArrowRight size={17} /></Button>
          </Link>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="landing-container landing-footer-inner">
          <div className="landing-brand">
            <Logo size={24} />
            <span className="brand-name">DevMatch</span>
          </div>
          <p className="landing-footer-text">Find developers who complement your skills.</p>
        </div>
      </footer>
    </div>
  )
}
