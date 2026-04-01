import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Mail, Lock, ArrowRight } from 'lucide-react';
import { supabase } from '../lib/supabase';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: name },
        },
      });

      if (error) {
        throw error;
      }
      
      // If email confirmation is required, handle it here, otherwise navigate.
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || "Failed to register. Please ensure your Supabase project is configured correctly.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container animate-fade-in">
      <div className="auth-card glass-panel">
        <div className="auth-header">
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem', color: 'var(--accent-primary)' }}>
            <User size={40} />
          </div>
          <h1>Create Account</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Get started with FinPilot-AI</p>
        </div>

        {error && (
          <div style={{ padding: '0.75rem', background: 'rgba(255, 71, 87, 0.1)', border: '1px solid var(--danger)', borderRadius: '12px', color: 'var(--danger)', fontSize: '0.9rem', textAlign: 'center' }}>
            {error}
          </div>
        )}

        <form className="auth-form" onSubmit={handleRegister}>
          <div className="form-group">
            <label className="label">Full Name</label>
            <div style={{ position: 'relative' }}>
              <User size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="text" 
                className="input-field" 
                style={{ paddingLeft: '2.5rem' }}
                placeholder="John Doe" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          </div>
          <div className="form-group">
            <label className="label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <Mail size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="email" 
                className="input-field" 
                style={{ paddingLeft: '2.5rem' }}
                placeholder="you@company.com" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>
          <div className="form-group">
            <label className="label">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="password" 
                className="input-field" 
                style={{ paddingLeft: '2.5rem' }}
                placeholder="••••••••" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={6}
                required
              />
            </div>
          </div>

          <button type="submit" className="btn-primary" style={{ marginTop: '0.5rem' }} disabled={loading}>
            {loading ? 'Creating Account...' : 'Continue'}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
