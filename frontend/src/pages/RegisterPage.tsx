import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Lock, Mail, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { errorMessage } from '../services/api'
import { AuthShell } from './LoginPage'

export default function RegisterPage() {
  const { register } = useAuth(); const navigate = useNavigate()
  const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [show, setShow] = useState(false); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(''); try { await register(name, email, password); navigate('/dashboard') } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) } }
  return <AuthShell title="Make your review process measurable" subtitle="Create a private workspace for document analysis and source review."><form className="auth-form" onSubmit={submit}><label>Full name<div className="input-wrap"><User size={17} /><input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" /></div></label><label>Email address<div className="input-wrap"><Mail size={17} /><input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@organization.com" /></div></label><label>Password<div className="input-wrap"><Lock size={17} /><input type={show ? 'text' : 'password'} required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" /><button type="button" className="input-action" onClick={() => setShow(!show)}>{show ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>{error && <div className="form-error">{error}</div>}<button className="button button-primary full" disabled={busy}>{busy ? 'Creating account…' : 'Create account'} <span>→</span></button></form><p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p></AuthShell>
}
