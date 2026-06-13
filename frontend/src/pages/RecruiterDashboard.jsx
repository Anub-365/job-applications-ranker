import { useState, useEffect } from 'react';
import { Briefcase, Plus, Users, Search, Filter, ChevronDown, ChevronUp, RefreshCw, ExternalLink, X } from 'lucide-react';
import api from '../api';

export default function RecruiterDashboard() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [posting, setPosting] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [filters, setFilters] = useState({ branch: '', skill: '', min_score: '' });
  const [expandedCandidate, setExpandedCandidate] = useState(null);
  const [rematching, setRematching] = useState(false);
  const [jobForm, setJobForm] = useState({ title: '', company: '', description: '', required_skills: '' });
  const [message, setMessage] = useState(null);

  const fetchJobs = async () => {
    try {
      const res = await api.get('/recruiters/jobs');
      setJobs(res.data);
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchJobs(); }, []);

  const handlePostJob = async (e) => {
    e.preventDefault();
    setPosting(true);
    setMessage(null);
    try {
      const payload = {
        ...jobForm,
        required_skills: jobForm.required_skills.split(',').map(s => s.trim()).filter(Boolean),
      };
      await api.post('/recruiters/jobs', payload);
      setMessage({ type: 'success', text: 'Job posted! Matching will begin in the background.' });
      setShowForm(false);
      setJobForm({ title: '', company: '', description: '', required_skills: '' });
      fetchJobs();
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to post job' });
    }
    setPosting(false);
  };

  const loadCandidates = async (jobId) => {
    setSelectedJob(jobId);
    setLoadingCandidates(true);
    try {
      const params = {};
      if (filters.branch) params.branch = filters.branch;
      if (filters.skill) params.skill = filters.skill;
      if (filters.min_score) params.min_score = parseFloat(filters.min_score);
      const res = await api.get(`/recruiters/jobs/${jobId}/candidates`, { params });
      setCandidates(res.data);
    } catch {}
    setLoadingCandidates(false);
  };

  const handleRematch = async (jobId) => {
    setRematching(true);
    try {
      await api.post(`/recruiters/jobs/${jobId}/rematch`);
      setMessage({ type: 'success', text: 'Rematching started! Refresh in a few seconds.' });
      setTimeout(() => loadCandidates(jobId), 3000);
    } catch {}
    setRematching(false);
  };

  const ScoreBadge = ({ score, label }) => {
    const cls = score >= 70 ? 'score-high' : score >= 40 ? 'score-mid' : 'score-low';
    return <span className={`score-badge ${cls}`}>{label}: {score.toFixed(0)}</span>;
  };

  if (loading) return <div className="flex justify-center py-20"><div className="spinner" /></div>;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 animate-fade-in">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Recruiter Dashboard</h1>
          <p className="text-dark-400 mt-1">Post jobs and find the best-matched candidates.</p>
        </div>
        <button id="create-job-btn" onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2">
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? 'Cancel' : 'Post Job'}
        </button>
      </div>

      {message && (
        <div className={`flex items-center gap-2 rounded-lg px-4 py-3 text-sm mb-6 ${message.type === 'success' ? 'bg-green-500/10 border border-green-500/30 text-green-400' : 'bg-red-500/10 border border-red-500/30 text-red-400'}`}>
          {message.text}
        </div>
      )}

      {/* Job Form */}
      {showForm && (
        <div className="glass-card p-6 mb-6 animate-slide-up">
          <h2 className="font-semibold text-white mb-4">New Job Posting</h2>
          <form onSubmit={handlePostJob} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-dark-300 mb-1.5 block">Job Title *</label>
                <input id="job-title" className="input-field" placeholder="e.g. Backend Developer Intern" value={jobForm.title} onChange={e => setJobForm(f => ({ ...f, title: e.target.value }))} required />
              </div>
              <div>
                <label className="text-sm text-dark-300 mb-1.5 block">Company</label>
                <input id="job-company" className="input-field" placeholder="e.g. Acme Inc." value={jobForm.company} onChange={e => setJobForm(f => ({ ...f, company: e.target.value }))} />
              </div>
            </div>
            <div>
              <label className="text-sm text-dark-300 mb-1.5 block">Description *</label>
              <textarea id="job-description" className="input-field" rows="4" placeholder="Describe the role, responsibilities, and requirements..." value={jobForm.description} onChange={e => setJobForm(f => ({ ...f, description: e.target.value }))} required />
            </div>
            <div>
              <label className="text-sm text-dark-300 mb-1.5 block">Required Skills (comma-separated)</label>
              <input id="job-skills" className="input-field" placeholder="e.g. Python, FastAPI, Docker, PostgreSQL" value={jobForm.required_skills} onChange={e => setJobForm(f => ({ ...f, required_skills: e.target.value }))} />
            </div>
            <button id="submit-job" type="submit" disabled={posting} className="btn-primary !py-3 flex items-center justify-center gap-2">
              {posting ? <div className="spinner !w-5 !h-5" /> : 'Post & Start Matching'}
            </button>
          </form>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Jobs List */}
        <div className="lg:col-span-1">
          <h2 className="font-semibold text-white mb-3 flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-brand-400" /> Your Jobs ({jobs.length})
          </h2>
          {jobs.length === 0 ? (
            <div className="glass-card p-6 text-center text-dark-400 text-sm">No jobs posted yet. Click "Post Job" to start.</div>
          ) : (
            <div className="space-y-2">
              {jobs.map(j => (
                <button
                  key={j.id}
                  onClick={() => loadCandidates(j.id)}
                  className={`w-full text-left glass-card p-4 transition-all ${selectedJob === j.id ? '!border-brand-500/50 !bg-brand-500/5' : ''}`}
                >
                  <h3 className="font-medium text-white text-sm">{j.title}</h3>
                  <p className="text-xs text-dark-500 mt-0.5">{j.company || 'No company'}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {(j.required_skills || []).slice(0, 3).map((s, i) => (
                      <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-dark-800 text-dark-400">{s}</span>
                    ))}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Candidates */}
        <div className="lg:col-span-2">
          {selectedJob ? (
            <>
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-semibold text-white flex items-center gap-2">
                  <Users className="w-4 h-4 text-brand-400" /> Candidates ({candidates.length})
                </h2>
                <button onClick={() => handleRematch(selectedJob)} disabled={rematching} className="btn-secondary !px-3 !py-1.5 text-xs flex items-center gap-1">
                  <RefreshCw className={`w-3 h-3 ${rematching ? 'animate-spin' : ''}`} /> Rematch
                </button>
              </div>

              {/* Filters */}
              <div className="flex gap-2 mb-4 flex-wrap">
                <input className="input-field !py-1.5 !text-xs w-32" placeholder="Filter branch" value={filters.branch} onChange={e => setFilters(f => ({ ...f, branch: e.target.value }))} />
                <input className="input-field !py-1.5 !text-xs w-32" placeholder="Filter skill" value={filters.skill} onChange={e => setFilters(f => ({ ...f, skill: e.target.value }))} />
                <input className="input-field !py-1.5 !text-xs w-28" placeholder="Min score" type="number" value={filters.min_score} onChange={e => setFilters(f => ({ ...f, min_score: e.target.value }))} />
                <button onClick={() => loadCandidates(selectedJob)} className="btn-primary !px-3 !py-1.5 text-xs"><Filter className="w-3 h-3" /></button>
              </div>

              {loadingCandidates ? (
                <div className="flex justify-center py-10"><div className="spinner" /></div>
              ) : candidates.length === 0 ? (
                <div className="glass-card p-8 text-center text-dark-400 text-sm">No candidates matched yet. Check back in a few seconds after posting.</div>
              ) : (
                <div className="space-y-3">
                  {candidates.map((c, idx) => (
                    <div key={c.match.id} className="glass-card p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-bold text-dark-500 bg-dark-800 px-2 py-0.5 rounded">#{idx + 1}</span>
                            <span className="font-semibold text-white">{c.student_name}</span>
                            <ScoreBadge score={c.match.final_score} label="Final" />
                          </div>
                          <div className="flex items-center gap-3 text-xs text-dark-400 mb-2">
                            <span>{c.student_email}</span>
                            {c.github_username && <span className="flex items-center gap-1"><ExternalLink className="w-3 h-3" /> @{c.github_username}</span>}
                            {c.branch && <span>{c.branch}</span>}
                            {c.cgpa > 0 && <span>CGPA: {c.cgpa}</span>}
                          </div>

                          {/* Score Breakdown */}
                          <div className="flex gap-2 flex-wrap mb-2">
                            <ScoreBadge score={c.match.semantic_score * 100} label="Semantic" />
                            <ScoreBadge score={c.match.github_score} label="GitHub" />
                            <ScoreBadge score={c.match.skill_score} label="Skill" />
                          </div>

                          {/* Skills */}
                          <div className="flex gap-1 flex-wrap mb-2">
                            {c.skills.slice(0, 6).map(sk => {
                              const isSelfReported = sk.level === 'Self-Reported';
                              return (
                                <span 
                                  key={sk.id} 
                                  title={isSelfReported ? "Self-Reported (No code evidence)" : `Verified Skill (${sk.level})`}
                                  className={`text-[10px] px-2 py-0.5 rounded border ${isSelfReported ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' : 'bg-green-500/10 text-green-400 border-green-500/20'}`}
                                >
                                  {sk.skill_name} {isSelfReported ? '👤' : '✓'}
                                </span>
                              );
                            })}
                            {c.skills.length > 6 && (
                              <span className="text-[10px] px-2 py-0.5 rounded border bg-dark-800 text-dark-400 border-dark-700">
                                +{c.skills.length - 6} more
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="flex flex-col items-end justify-between h-full py-1">
                          <button onClick={() => setExpandedCandidate(expandedCandidate === c.match.id ? null : c.match.id)} className="text-dark-500 hover:text-white p-1 transition-colors bg-dark-800 rounded mb-2">
                            {expandedCandidate === c.match.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>

                      {/* Expanded Details */}
                      {expandedCandidate === c.match.id && (
                        <div className="mt-3 pt-3 border-t border-dark-800 animate-fade-in">
                          <h4 className="text-xs font-semibold text-dark-300 mb-1.5">Match Explanation</h4>
                          <p className="text-xs text-dark-400 whitespace-pre-line mb-3">{c.match.explanation}</p>

                          {c.match.top_project_title && (
                            <div className="text-xs mb-3">
                              <span className="text-dark-300 font-medium">Top Project: </span>
                              <span className="text-brand-300">{c.match.top_project_title}</span>
                            </div>
                          )}

                          {c.top_projects.length > 0 && (
                            <div>
                              <h4 className="text-xs font-semibold text-dark-300 mb-1.5">Projects</h4>
                              <div className="space-y-2">
                                {c.top_projects.map(p => (
                                  <div key={p.id} className="bg-dark-900/60 rounded-lg p-3">
                                    <div className="font-medium text-white text-xs">{p.title}</div>
                                    <p className="text-xs text-dark-400 mt-0.5 line-clamp-2">{p.description}</p>
                                    <div className="flex gap-1 mt-1 flex-wrap">
                                      {p.tech_stack.map((t, i) => (
                                        <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-dark-800 text-dark-400">{t}</span>
                                      ))}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="glass-card p-12 text-center text-dark-400">
              <Search className="w-12 h-12 mx-auto mb-4 text-dark-600" />
              <p className="text-sm">Select a job to view matched candidates</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
