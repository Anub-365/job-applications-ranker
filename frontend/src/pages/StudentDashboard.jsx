import { useState, useEffect } from 'react';
import { Upload, Github, FileText, AlertCircle, CheckCircle, RefreshCw, Briefcase } from 'lucide-react';
import api from '../api';

export default function StudentDashboard() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [ghUser, setGhUser] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [profileForm, setProfileForm] = useState({ cgpa: '', branch: '' });
  const [message, setMessage] = useState(null);
  const [matches, setMatches] = useState([]);
  const [allExtractedSkills, setAllExtractedSkills] = useState(null); // RAW skills from upload

  const fetchProfile = async () => {
    try {
      const res = await api.get('/students/profile');
      setProfile(res.data);
      
      //dev-2
      console.log("hi")

      
      setGhUser(res.data.github_username || '');
      setProfileForm({ cgpa: res.data.cgpa || '', branch: res.data.branch || '' });
    } catch {}
    setLoading(false);
  };

  const fetchMatches = async () => {
    try {
      const res = await api.get('/students/matches');
      setMatches(res.data);
    } catch {}
  };

  useEffect(() => { fetchProfile(); fetchMatches(); }, []);

  const handleResumeUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setMessage(null);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await api.post('/students/upload-resume', fd);
      setMessage({ 
        type: 'success', 
        text: `Resume processed by ${res.data.llm_used}! Found ${res.data.skills_found} skills and ${res.data.projects_found} projects.` 
      });
      setAllExtractedSkills(res.data.all_skills || null);
      fetchProfile();
    } catch (err) {
      if (err.response?.status === 429) {
        setMessage({ type: 'error', text: 'OpenAI API quota exceeded. Please check your API key or billing plan.' });
      } else {
        setMessage({ type: 'error', text: err.response?.data?.detail || 'Upload failed' });
      }
    }
    setUploading(false);
  };

  const handleGithubConnect = async () => {
    if (!ghUser.trim()) return;
    setConnecting(true);
    setMessage(null);
    try {
      await api.put('/students/profile', { github_username: ghUser });
      const res = await api.post('/students/connect-github');
      setMessage({ 
        type: 'success', 
        text: `GitHub connected via ${res.data.llm_used}! Score: ${res.data.scores.total_score}/100` 
      });

      //dev-1
      console.log(res.data);


      fetchProfile();
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'GitHub connection failed' });
    }
    setConnecting(false);
  };

  const handleSaveProfile = async () => {
    try {
      await api.put('/students/profile', {
        cgpa: parseFloat(profileForm.cgpa) || 0,
        branch: profileForm.branch,
      });
      setMessage({ type: 'success', text: 'Profile updated!' });
      setEditMode(false);
      fetchProfile();
    } catch (err) {
      setMessage({ type: 'error', text: 'Update failed' });
    }
  };

  if (loading) return <div className="flex justify-center py-20"><div className="spinner" /></div>;

  const ScoreBadge = ({ score, label }) => {
    const cls = score >= 70 ? 'score-high' : score >= 40 ? 'score-mid' : 'score-low';
    return <span className={`score-badge ${cls}`}>{label}: {score.toFixed(0)}%</span>;
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 animate-fade-in">
      <h1 className="text-3xl font-bold gradient-text mb-2">Student Dashboard</h1>
      <p className="text-dark-400 mb-8">Upload your resume, connect GitHub, and track your matches.</p>

      {message && (
        <div className={`flex items-center gap-2 rounded-lg px-4 py-3 text-sm mb-6 ${message.type === 'success' ? 'bg-green-500/10 border border-green-500/30 text-green-400' : 'bg-red-500/10 border border-red-500/30 text-red-400'}`}>
          {message.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {message.text}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Resume Upload */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="w-5 h-5 text-brand-400" />
            <h2 className="font-semibold text-white">Resume</h2>
          </div>
          {profile?.processing_status === 'done' ? (
            <div className="text-sm text-green-400 mb-3 flex items-center gap-1"><CheckCircle className="w-4 h-4" /> Processed</div>
          ) : profile?.processing_status === 'processing' ? (
            <div className="text-sm text-yellow-400 mb-3 flex items-center gap-1"><RefreshCw className="w-4 h-4 animate-spin" /> Processing...</div>
          ) : null}
          <label className={`flex flex-col items-center gap-3 border-2 border-dashed rounded-xl p-6 cursor-pointer transition-colors ${uploading ? 'border-brand-500/50 bg-brand-500/5' : 'border-dark-700 hover:border-brand-500/40'}`}>
            {uploading ? <div className="spinner" /> : <Upload className="w-8 h-8 text-dark-500" />}
            <span className="text-sm text-dark-400">{uploading ? 'Processing...' : 'Drop PDF or click to upload'}</span>
            <input id="resume-upload" type="file" accept=".pdf" className="hidden" onChange={handleResumeUpload} disabled={uploading} />
          </label>
        </div>

        {/* GitHub Connect */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Github className="w-5 h-5 text-brand-400" />
            <h2 className="font-semibold text-white">GitHub</h2>
          </div>
          {profile?.github_metrics ? (
            <div className="mb-3">
              <div className="text-sm text-green-400 flex items-center gap-1 mb-2"><CheckCircle className="w-4 h-4" /> Connected: @{profile.github_username}</div>
              <ScoreBadge score={profile.github_metrics.total_score} label="Score" />
              <p className="text-xs text-dark-400 mt-2 leading-relaxed">{profile.github_metrics.summary}</p>
            </div>
          ) : null}
          <div className="flex gap-2 mt-3">
            <input id="github-username" className="input-field !py-2 text-sm flex-1" placeholder="GitHub username" value={ghUser} onChange={e => setGhUser(e.target.value)} />
            <button id="github-connect" onClick={handleGithubConnect} disabled={connecting} className="btn-primary !px-4 !py-2 text-sm whitespace-nowrap">
              {connecting ? <div className="spinner !w-4 !h-4" /> : 'Connect'}
            </button>
          </div>
        </div>

        {/* Profile Info */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-white">Profile</h2>
            <button onClick={() => setEditMode(!editMode)} className="text-sm text-brand-400 hover:text-brand-300">{editMode ? 'Cancel' : 'Edit'}</button>
          </div>
          {editMode ? (
            <div className="space-y-3">
              <div>
                <label className="text-xs text-dark-400 mb-1 block">CGPA</label>
                <input className="input-field !py-2 text-sm" type="number" step="0.1" max="10" value={profileForm.cgpa} onChange={e => setProfileForm(f => ({ ...f, cgpa: e.target.value }))} />
              </div>
              <div>
                <label className="text-xs text-dark-400 mb-1 block">Branch</label>
                <input className="input-field !py-2 text-sm" placeholder="e.g. Computer Science" value={profileForm.branch} onChange={e => setProfileForm(f => ({ ...f, branch: e.target.value }))} />
              </div>
              <button onClick={handleSaveProfile} className="btn-primary !py-2 w-full text-sm">Save</button>
            </div>
          ) : (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-dark-400">CGPA</span><span className="text-white">{profile?.cgpa || '—'}</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Branch</span><span className="text-white">{profile?.branch || '—'}</span></div>
              <div className="flex justify-between"><span className="text-dark-400">Status</span><span className="capitalize text-white">{profile?.processing_status || 'idle'}</span></div>
            </div>
          )}
        </div>
      </div>

      {/* Extracted Resume Text */}
      {profile?.resume_text && (
        <div className="glass-card p-6 mt-6">
          <h2 className="font-semibold text-white mb-4">Extracted Resume Text</h2>
          <div className="bg-dark-900/50 rounded-xl p-4 border border-dark-800 max-h-60 overflow-y-auto w-full text-xs text-dark-300 font-mono whitespace-pre-wrap">
            {profile.resume_text}
          </div>
        </div>
      )}

      {/* Raw Extracted Skills (Debug) */}
      {allExtractedSkills && (
        <div className="glass-card p-6 mt-6 border-brand-500/20">
          <h2 className="font-semibold text-white mb-4">AI Skill Analysis (Triangulation Model)</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allExtractedSkills.map((sk, idx) => {
              const isRejected = sk.is_blacklisted || sk.confidence_score < 30.0;
              return (
                <div key={idx} className={`flex flex-col gap-1 p-3 rounded-lg border ${isRejected ? 'bg-red-500/5 border-red-500/20' : sk.is_self_reported ? 'bg-yellow-500/5 border-yellow-500/20' : 'bg-green-500/5 border-green-500/20'}`}>
                  <div className="flex justify-between items-start">
                    <span className={`text-sm font-medium ${isRejected ? 'text-dark-300 line-through' : 'text-white'}`}>{sk.skill_name}</span>
                    <span className="text-xs text-dark-400 font-mono">{sk.confidence_score.toFixed(0)}%</span>
                  </div>
                  {sk.evidence && (
                    <div className="text-[10px] text-dark-500 flex gap-2 mt-1">
                      <span>Resume: {sk.evidence.base}%</span>
                      <span>Project: {sk.evidence.project}%</span>
                      <span>GitHub: {sk.evidence.execution}%</span>
                    </div>
                  )}
                  <div className="text-[10px] text-dark-400 flex flex-wrap gap-1">
                    {sk.is_blacklisted && <span className="text-red-400">Blacklisted</span>}
                    {sk.confidence_score < 30.0 && !sk.is_blacklisted && <span className="text-yellow-400">Low Confidence</span>}
                    {sk.is_self_reported && !isRejected && <span className="text-yellow-400">Self-Reported</span>}
                    {!isRejected && !sk.is_self_reported && <span className="text-green-400">Verified & Saved</span>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Skills */}
      {profile?.skills?.length > 0 && (
        <div className="glass-card p-6 mt-6">
          <h2 className="font-semibold text-white mb-4">Skills & Confidence</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {profile.skills.map(sk => (
              <div key={sk.id} className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium text-dark-200">{sk.skill_name}</span>
                    <span className="text-xs text-dark-400">{sk.confidence_score.toFixed(0)}% · {sk.level}</span>
                  </div>
                  <div className="skill-bar"><div className="skill-bar-fill" style={{ width: `${sk.confidence_score}%` }} /></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Projects */}
      {profile?.projects?.length > 0 && (
        <div className="glass-card p-6 mt-6">
          <h2 className="font-semibold text-white mb-4">Projects</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {profile.projects.map(p => (
              <div key={p.id} className="bg-dark-900/50 rounded-xl p-4 border border-dark-800">
                <h3 className="font-medium text-white mb-1">{p.title}</h3>
                <p className="text-xs text-dark-400 mb-2 line-clamp-2">{p.description}</p>
                <div className="flex flex-wrap gap-1.5">
                  {p.tech_stack.map((t, i) => (
                    <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-brand-500/10 text-brand-300 border border-brand-500/20">{t}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Matches */}
      {matches.length > 0 && (
        <div className="glass-card p-6 mt-6">
          <div className="flex items-center gap-2 mb-4">
            <Briefcase className="w-5 h-5 text-brand-400" />
            <h2 className="font-semibold text-white">Your Matches</h2>
          </div>
          <div className="space-y-3">
            {matches.map(m => (
              <div key={m.id} className="bg-dark-900/50 rounded-xl p-4 border border-dark-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-white">{m.top_project_title || 'Job Match'}</span>
                    <ScoreBadge score={m.final_score} label="Score" />
                  </div>
                  <p className="text-xs text-dark-400 whitespace-pre-line">{m.explanation}</p>
                </div>
                <div className="text-right text-xs text-dark-500 space-y-0.5">
                  <div>Semantic: {(m.semantic_score * 100).toFixed(0)}%</div>
                  <div>GitHub: {m.github_score.toFixed(0)}</div>
                  <div>Skill: {m.skill_score.toFixed(0)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
