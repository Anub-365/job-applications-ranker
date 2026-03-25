import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { Sparkles, LogOut, User } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="sticky top-0 z-50 glass-card !rounded-none border-x-0 border-t-0 px-6 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <Sparkles className="w-6 h-6 text-brand-400 group-hover:text-brand-300 transition-colors" />
          <span className="text-lg font-bold gradient-text">Internship Connect</span>
        </Link>

        <div className="flex items-center gap-4">
          {user ? (
            <>
              <div className="flex items-center gap-2 text-sm text-dark-300">
                <User className="w-4 h-4" />
                <span>{user.name}</span>
                <span className="score-badge score-mid !text-xs capitalize">{user.role}</span>
              </div>
              <button onClick={handleLogout} className="btn-secondary !px-3 !py-1.5 flex items-center gap-1.5 text-sm">
                <LogOut className="w-4 h-4" /> Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-secondary !py-1.5 text-sm">Log In</Link>
              <Link to="/register" className="btn-primary !py-1.5 text-sm">Sign Up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
