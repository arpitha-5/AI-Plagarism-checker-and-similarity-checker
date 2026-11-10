import { useState, type ReactNode, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, FileSearch, Lock, Mail } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { errorMessage } from '../services/api'

export default function LoginPage() {
  const { login } = useAuth(); const navigate = useNavigate(); const location = useLocation()
  const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [show, setShow] = useState(false); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(''); try { await login(email, password); navigate((location.state as { from?: string })?.from || '/dashboard') } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) } }
  return <AuthShell title="Welcome back" subtitle="Sign in to continue your evidence-first analysis workspace."><form className="auth-form" onSubmit={submit}><label>Email address<div className="input-wrap"><Mail size={17} /><input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@organization.com" /></div></label><label>Password<div className="input-wrap"><Lock size={17} /><input type={show ? 'text' : 'password'} required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your password" /><button type="button" className="input-action" onClick={() => setShow(!show)}>{show ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>{error && <div className="form-error">{error}</div>}<button className="button button-primary full" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'} <span>→</span></button></form><p className="auth-switch">New to PlagiarismAI? <Link to="/register">Create an account</Link></p></AuthShell>
}

export function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return <div className="auth-page"><div className="auth-brand"><Link to="/" className="saas-brand"><span className="brand-icon"><FileSearch size={20} /></span><span><b>PlagiarismAI</b><small>Evidence-first text intelligence</small></span></Link></div><div className="auth-card"><div className="auth-card-copy"><span className="eyebrow">Secure workspace</span><h1>{title}</h1><p>{subtitle}</p><div className="auth-benefit"><FileSearch size={18} /><span>Analyze with transparent, explainable signals.</span></div></div><div className="auth-card-form"><h2>Account access</h2>{children}</div></div></div>
}
