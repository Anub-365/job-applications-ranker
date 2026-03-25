import { Link } from 'react-router-dom';
import { Sparkles, Search, Github, BarChart3, Brain, Zap, Shield } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative py-24 px-6 text-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-brand-900/20 via-transparent to-transparent" />
        <div className="absolute top-20 left-1/4 w-72 h-72 bg-brand-600/10 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute top-40 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1.5s' }} />

        <div className="relative max-w-4xl mx-auto animate-fade-in">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-300 text-sm mb-8">
            <Sparkles className="w-4 h-4" /> AI-Powered Matching
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold mb-6">
            <span className="gradient-text">Find Your Perfect</span><br/>
            <span className="text-white">Internship Match</span>
          </h1>
          <p className="text-lg md:text-xl text-dark-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Beyond keyword matching — we use semantic AI, GitHub intelligence, and skill confidence scoring
            to connect students with the right opportunities.
          </p>
          <div className="flex gap-4 justify-center">
            <Link to="/register" className="btn-primary !px-8 !py-3 text-base">Get Started Free</Link>
            <a href="#features" className="btn-secondary !px-8 !py-3 text-base">Learn More</a>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-4 gradient-text">How It Works</h2>
          <p className="text-center text-dark-400 mb-16 max-w-xl mx-auto">Our AI understands developer skills at a deeper level than traditional platforms</p>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: Search, title: 'Semantic Search', desc: 'We understand intent, not just keywords. "Built REST APIs" matches "Backend Developer" automatically.' },
              { icon: Github, title: 'GitHub Intelligence', desc: 'We analyze repos, commits, and contributions to verify real coding ability — not just listed skills.' },
              { icon: Brain, title: 'Skill Confidence', desc: 'Each skill gets a confidence score backed by evidence from code, projects, and activity.' },
              { icon: BarChart3, title: 'Explainable Rankings', desc: 'Every match includes a breakdown showing exactly why a candidate was ranked where they are.' },
              { icon: Zap, title: 'Instant Matching', desc: 'Post a job and get AI-ranked candidates in seconds, not days of manual screening.' },
              { icon: Shield, title: 'Cold Start Ready', desc: 'No GitHub? No problem. Our adaptive scoring adjusts when data is limited.' },
            ].map((f, i) => (
              <div key={i} className="glass-card p-6 animate-slide-up" style={{ animationDelay: `${i * 0.1}s` }}>
                <f.icon className="w-10 h-10 text-brand-400 mb-4" />
                <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-dark-400 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-2xl mx-auto text-center glass-card p-12">
          <h2 className="text-3xl font-bold mb-4 text-white">Ready to connect?</h2>
          <p className="text-dark-400 mb-8">Join as a student or recruiter — matching begins instantly.</p>
          <div className="flex gap-4 justify-center">
            <Link to="/register" className="btn-primary !px-8 !py-3">Sign Up as Student</Link>
            <Link to="/register" className="btn-secondary !px-8 !py-3">Sign Up as Recruiter</Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-dark-800 py-8 px-6 text-center text-dark-500 text-sm">
        © 2026 Internship Connect. Built with AI.
      </footer>
    </div>
  );
}
