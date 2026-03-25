import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { UserPlus } from 'lucide-react';
import api from '../api';

export default function Register() {
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'student' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const update = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/auth/register', form);
      login(
        { id: res.data.user_id, name: res.data.name, role: res.data.role },
        res.data.access_token
      );
      navigate(res.data.role === 'student' ? '/dashboard' : '/recruiter');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-6">
      <div className="glass-card p-8 w-full max-w-md animate-fade-in">
        <div className="text-center mb-8">
          <UserPlus className="w-10 h-10 text-brand-400 mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-white">Create Account</h1>
          <p className="text-dark-400 text-sm mt-1">Join the smart matching platform</p>
        </div>

        {error && <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-4 py-2 text-sm mb-4">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1.5">Full Name</label>
            <input id="register-name" className="input-field" placeholder="John Doe" value={form.name} onChange={e => update('name', e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1.5">Email</label>
            <input id="register-email" type="email" className="input-field" placeholder="you@example.com" value={form.email} onChange={e => update('email', e.target.value)} required />
          </div>
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-1.5">Password</label>
            <input id="register-password" type="password" className="input-field" placeholder="Min. 6 characters" value={form.password} onChange={e => update('password', e.target.value)} required minLength={6} />
          </div>
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-3">I am a</label>
            <div className="grid grid-cols-2 gap-3">
              {['student', 'recruiter'].map(role => (
                <button
                  key={role}
                  type="button"
                  id={`register-role-${role}`}
                  onClick={() => update('role', role)}
                  className={`py-3 rounded-xl text-sm font-semibold capitalize transition-all duration-200 border ${
                    form.role === role
                      ? 'bg-brand-600/20 border-brand-500 text-brand-300'
                      : 'bg-dark-900/50 border-dark-700 text-dark-400 hover:border-dark-500'
                  }`}
                >
                  {role === 'student' ? '🎓 Student' : '🏢 Recruiter'}
                </button>
              ))}
            </div>
          </div>
          <button id="register-submit" type="submit" disabled={loading} className="btn-primary w-full !py-3 flex items-center justify-center gap-2">
            {loading ? <div className="spinner !w-5 !h-5" /> : 'Create Account'}
          </button>
        </form>

        <p className="text-center text-dark-400 text-sm mt-6">
          Already have an account? <Link to="/login" className="text-brand-400 hover:text-brand-300">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
