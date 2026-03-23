import { useState } from 'react';
import { uploadResume, searchJobs, ResumeResponse, JobMatch } from './services/api';
import { Upload, Search, Briefcase, CheckCircle, XCircle, Copy, ExternalLink, ChevronRight, Loader } from 'lucide-react';

type Step = 'upload' | 'search' | 'results';

const PROGRESS_STEPS = [
  { id: 'fetch',   label: 'Fetching jobs from RapidAPI + SerpApi' },
  { id: 'embed',   label: 'Embedding resume & job descriptions' },
  { id: 'match',   label: 'Scoring matches with hybrid algorithm' },
  { id: 'analyze', label: 'Analyzing match reasons with GPT-4o' },
  { id: 'letter',  label: 'Generating personalized cover letters' },
];

function getScoreClass(score: number) {
  if (score >= 0.70) return { text: 'score-green', badge: 'badge-green', label: 'Strong Match' };
  if (score >= 0.50) return { text: 'score-yellow', badge: 'badge-yellow', label: 'Good Match' };
  return { text: 'score-red', badge: 'badge-red', label: 'Weak Match' };
}

export default function App() {
  const [step, setStep] = useState<Step>('upload');
  const [resume, setResume] = useState<ResumeResponse | null>(null);
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobMatch | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [progressStep, setProgressStep] = useState(-1);
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [topK, setTopK] = useState(5);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const result = await uploadResume(file);
      setResume(result);
      setQuery(result.job_titles[0] || '');
      setStep('search');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload resume.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!resume) return;
    setLoading(true);
    setError(null);
    setProgressStep(0);
    const interval = setInterval(() => {
      setProgressStep(prev => {
        if (prev >= PROGRESS_STEPS.length - 1) { clearInterval(interval); return prev; }
        return prev + 1;
      });
    }, 3500);
    try {
      const result = await searchJobs(resume.resume_id, query, location, remoteOnly, topK);
      clearInterval(interval);
      setProgressStep(PROGRESS_STEPS.length);
      setMatches(result.matches);
      setSelectedJob(result.matches[0] || null);
      setStep('results');
    } catch (err: any) {
      clearInterval(interval);
      setError(err.response?.data?.detail || 'Job search failed.');
    } finally {
      setLoading(false);
      setProgressStep(-1);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen gradient-bg" style={{ backgroundColor: '#080C14' }}>

      {/* Header */}
      <header style={{ borderBottom: '1px solid #1E2433', backgroundColor: '#080C14' }} className="px-8 py-4 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div style={{ backgroundColor: '#3B82F6', borderRadius: '8px' }} className="w-8 h-8 flex items-center justify-center">
              <Briefcase size={16} className="text-white" />
            </div>
            <span className="mono font-bold text-white text-sm tracking-tight">ai-job-assistant</span>
          </div>

          {/* Step indicator */}
          <div className="flex items-center gap-1">
            {(['upload', 'search', 'results'] as Step[]).map((s, i) => (
              <div key={s} className="flex items-center gap-1">
                <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs transition-all ${step === s ? 'text-blue-400' : 'text-gray-600'}`}
                  style={{ backgroundColor: step === s ? 'rgba(59,130,246,0.1)' : 'transparent' }}>
                  <span className={`w-4 h-4 rounded-full flex items-center justify-center text-xs font-bold ${step === s ? 'bg-blue-500 text-white' : 'text-gray-600'}`}
                    style={{ backgroundColor: step === s ? '#3B82F6' : '#1E2433' }}>
                    {i + 1}
                  </span>
                  <span className="mono">{s}</span>
                </div>
                {i < 2 && <ChevronRight size={12} className="text-gray-700" />}
              </div>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-8 py-12">

        {/* Error */}
        {error && (
          <div className="mb-8 px-4 py-3 rounded-lg text-sm fade-in"
            style={{ backgroundColor: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)', color: '#F87171' }}>
            {error}
          </div>
        )}

        {/* ── Step 1: Upload ── */}
        {step === 'upload' && (
          <div className="max-w-xl mx-auto fade-in">
            <div className="mb-10">
              <p className="mono text-blue-400 text-xs tracking-widest uppercase mb-3">Step 01</p>
              <h2 className="mono font-bold text-white text-4xl leading-tight mb-3">
                Upload<br />your resume.
              </h2>
              <p style={{ color: '#94A3B8' }} className="text-sm leading-relaxed">
                AI extracts your skills, experience, and education — then finds the best matching jobs and writes personalized cover letters.
              </p>
            </div>

            <label className={`block rounded-xl p-12 text-center cursor-pointer transition-all ${loading ? '' : 'hover:glow'}`}
              style={{
                backgroundColor: '#111827',
                border: loading ? '1px solid #3B82F6' : '1px dashed #1E2433',
              }}>
              <input type="file" accept=".pdf" onChange={handleFileUpload} className="hidden" disabled={loading} />
              {loading ? (
                <div className="flex flex-col items-center gap-4">
                  <Loader size={32} className="text-blue-400 animate-spin" />
                  <div>
                    <p className="mono text-blue-400 text-sm font-medium">Parsing resume...</p>
                    <p style={{ color: '#64748B' }} className="text-xs mt-1">Extracting skills with GPT-4o</p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-4">
                  <div className="w-14 h-14 rounded-xl flex items-center justify-center"
                    style={{ backgroundColor: '#1E2433' }}>
                    <Upload size={24} style={{ color: '#3B82F6' }} />
                  </div>
                  <div>
                    <p className="text-white font-medium text-sm">Drop your PDF here</p>
                    <p style={{ color: '#64748B' }} className="text-xs mt-1">or click to browse · max 10MB</p>
                  </div>
                </div>
              )}
            </label>

            {/* Features */}
            <div className="grid grid-cols-3 gap-3 mt-6">
              {[
                { icon: '⚡', label: 'Skill inference' },
                { icon: '🎯', label: 'Hybrid matching' },
                { icon: '✍️', label: 'Cover letters' },
              ].map(f => (
                <div key={f.label} className="px-3 py-2.5 rounded-lg text-center"
                  style={{ backgroundColor: '#111827', border: '1px solid #2D3748' }}>
                  <p className="text-base mb-1">{f.icon}</p>
                  <p style={{ color: '#94A3B8' }} className="text-xs">{f.label}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Step 2: Search ── */}
        {step === 'search' && resume && (
          <div className="max-w-2xl mx-auto fade-in">
            <div className="mb-8">
              <p className="mono text-blue-400 text-xs tracking-widest uppercase mb-3">Step 02</p>
              <h2 className="mono font-bold text-white text-3xl mb-2">Find your jobs.</h2>
              <p style={{ color: '#94A3B8' }} className="text-sm">Resume parsed successfully. Configure your search below.</p>
            </div>

            {/* Resume card */}
            <div className="rounded-xl p-5 mb-6 fade-in"
              style={{ backgroundColor: '#111827', border: '1px solid #2D3748' }}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle size={14} className="text-green-400" />
                  <span className="mono text-xs text-white font-medium">resume.parsed</span>
                </div>
                <span style={{ color: '#64748B' }} className="mono text-xs">{resume.skills.length} skills · {resume.experience_years}y exp</span>
              </div>
              <p style={{ color: '#6B7280' }} className="text-xs leading-relaxed mb-4">{resume.summary}</p>
              <div className="flex flex-wrap gap-1.5">
                {resume.skills.slice(0, 10).map(skill => (
                  <span key={skill} className="badge-blue px-2 py-0.5 rounded-md text-xs">{skill}</span>
                ))}
                {resume.skills.length > 10 && (
                  <span className="badge-gray px-2 py-0.5 rounded-md text-xs">+{resume.skills.length - 10}</span>
                )}
              </div>
            </div>

            {/* Search form */}
            <div className="rounded-xl p-6 space-y-4"
              style={{ backgroundColor: '#111827', border: '1px solid #2D3748' }}>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label style={{ color: '#94A3B8' }} className="block text-xs mono mb-2">query</label>
                  <input type="text" value={query} onChange={e => setQuery(e.target.value)}
                    placeholder="cybersecurity engineer"
                    className="input w-full px-3 py-2.5 text-sm" />
                </div>
                <div>
                  <label style={{ color: '#94A3B8' }} className="block text-xs mono mb-2">location</label>
                  <input type="text" value={location} onChange={e => setLocation(e.target.value)}
                    placeholder="India, Remote"
                    className="input w-full px-3 py-2.5 text-sm" />
                </div>
              </div>

              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={remoteOnly} onChange={e => setRemoteOnly(e.target.checked)}
                    className="rounded accent-blue-500" />
                  <span style={{ color: '#6B7280' }} className="text-xs">Remote only</span>
                </label>
                <div className="flex items-center gap-2">
                  <span style={{ color: '#6B7280' }} className="text-xs mono">top_k =</span>
                  <select value={topK} onChange={e => setTopK(Number(e.target.value))}
                    className="input px-2 py-1 text-xs mono">
                    {[3, 5, 10].map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
              </div>

              {/* Progress */}
              {loading && progressStep >= 0 && (
                <div className="rounded-lg p-4 space-y-2.5 fade-in"
                  style={{ backgroundColor: '#080C14', border: '1px solid #2D3748' }}>
                  {PROGRESS_STEPS.map((ps, i) => (
                    <div key={ps.id} className="flex items-center gap-3">
                      {i < progressStep ? (
                        <CheckCircle size={12} className="text-green-400 shrink-0" />
                      ) : i === progressStep ? (
                        <div className="w-3 h-3 rounded-full bg-blue-500 pulse shrink-0" />
                      ) : (
                        <div className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: '#1E2433' }} />
                      )}
                      <span className={`text-xs mono ${i < progressStep ? 'text-green-400' : i === progressStep ? 'text-blue-400' : ''}`}
                        style={{ color: i >= progressStep + 1 ? '#2A3347' : undefined }}>
                        {ps.label}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <button onClick={handleSearch} disabled={loading}
                className="btn-primary w-full py-2.5 text-sm flex items-center justify-center gap-2">
                {loading ? (
                  <><Loader size={14} className="animate-spin" /> Processing...</>
                ) : (
                  <><Search size={14} /> Search Jobs</>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Results ── */}
        {step === 'results' && (
          <div className="fade-in">
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="mono text-blue-400 text-xs tracking-widest uppercase mb-1">Step 03</p>
                <h2 className="mono font-bold text-white text-2xl">
                  {matches.length} matches found.
                </h2>
              </div>
              <button onClick={() => setStep('search')}
                style={{ color: '#64748B', border: '1px solid #2D3748', borderRadius: '8px' }}
                className="px-4 py-2 text-xs mono hover:text-white transition-colors">
                ← new search
              </button>
            </div>

            <div className="grid grid-cols-3 gap-5">

              {/* Job list */}
              <div className="col-span-1 space-y-2">
                {matches.map((match) => {
                  const sc = getScoreClass(match.match_score);
                  const isSelected = selectedJob?.job.job_id === match.job.job_id;
                  return (
                    <div key={match.job.job_id} onClick={() => setSelectedJob(match)}
                      className="rounded-xl p-4 cursor-pointer transition-all"
                      style={{
                        backgroundColor: isSelected ? '#0F1623' : '#0D1117',
                        border: isSelected ? '1px solid #3B82F6' : '1px solid #1E2433',
                      }}>
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="text-white text-xs font-medium leading-tight pr-2 line-clamp-2">{match.job.title}</h3>
                        <span className={`mono text-sm font-bold shrink-0 ${sc.text}`}>
                          {Math.round(match.match_score * 100)}%
                        </span>
                      </div>
                      <p style={{ color: '#94A3B8' }} className="text-xs mb-2">{match.job.company}</p>
                      <div className="flex flex-wrap gap-1">
                        <span className={`${sc.badge} px-2 py-0.5 rounded-md text-xs mono`}>{sc.label}</span>
                        {match.job.remote && <span className="badge-purple px-2 py-0.5 rounded-md text-xs">remote</span>}
                        {match.job.source && <span className="badge-gray px-2 py-0.5 rounded-md text-xs">{match.job.source}</span>}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Job detail */}
              {selectedJob && (() => {
                const sc = getScoreClass(selectedJob.match_score);
                return (
                  <div className="col-span-2 space-y-4">

                    {/* Header card */}
                    <div className="rounded-xl p-6"
                      style={{ backgroundColor: '#111827', border: '1px solid #2D3748' }}>
                      <div className="flex justify-between items-start mb-5">
                        <div className="flex-1 pr-4">
                          <h2 className="mono font-bold text-white text-lg leading-tight mb-1">
                            {selectedJob.job.title}
                          </h2>
                          <p style={{ color: '#94A3B8' }} className="text-sm flex items-center gap-2 flex-wrap">
                            {selectedJob.job.company} · {selectedJob.job.location}
                            {selectedJob.job.source && (
                              <span className="badge-gray px-2 py-0.5 rounded-md text-xs">
                                {selectedJob.job.source}
                              </span>
                            )}
                          </p>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <div className={`text-center px-4 py-2 rounded-xl ${sc.badge}`}>
                            <div className={`mono text-2xl font-bold ${sc.text}`}>
                              {Math.round(selectedJob.match_score * 100)}%
                            </div>
                            <div className={`text-xs mono ${sc.text}`}>{sc.label}</div>
                          </div>
                          {selectedJob.job.apply_link && (
                            <a href={selectedJob.job.apply_link} target="_blank" rel="noreferrer"
                              className="btn-primary flex items-center gap-1.5 px-4 py-2 text-xs mono">
                              apply <ExternalLink size={11} />
                            </a>
                          )}
                        </div>
                      </div>

                      {/* Match reasons */}
                      <div className="mb-5">
                        <p style={{ color: '#64748B' }} className="mono text-xs uppercase tracking-widest mb-3">Why you match</p>
                        <ul className="space-y-2">
                          {selectedJob.match_reasons.map((reason, i) => (
                            <li key={i} className="flex items-start gap-2.5">
                              <CheckCircle size={13} className="text-green-400 shrink-0 mt-0.5" />
                              <span style={{ color: '#CBD5E1' }} className="text-xs leading-relaxed">{reason}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Missing skills */}
                      {selectedJob.missing_skills.length > 0 && (
                        <div>
                          <p style={{ color: '#64748B' }} className="mono text-xs uppercase tracking-widest mb-3">Skills to develop</p>
                          <ul className="space-y-2">
                            {selectedJob.missing_skills.map((skill, i) => (
                              <li key={i} className="flex items-start gap-2.5">
                                <XCircle size={13} className="text-red-400 shrink-0 mt-0.5" />
                                <span style={{ color: '#CBD5E1' }} className="text-xs leading-relaxed">{skill}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Cover letter */}
                    {selectedJob.cover_letter && (
                      <div className="rounded-xl p-6"
                        style={{ backgroundColor: '#111827', border: '1px solid #2D3748' }}>
                        <div className="flex justify-between items-center mb-5">
                          <p style={{ color: '#64748B' }} className="mono text-xs uppercase tracking-widest">Cover Letter</p>
                          <button onClick={() => handleCopy(selectedJob.cover_letter!)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs mono transition-all"
                            style={{
                              color: copied ? '#34D399' : '#4B5563',
                              border: `1px solid ${copied ? 'rgba(52,211,153,0.3)' : '#1E2433'}`,
                              backgroundColor: copied ? 'rgba(52,211,153,0.08)' : 'transparent'
                            }}>
                            <Copy size={11} />
                            {copied ? 'copied!' : 'copy'}
                          </button>
                        </div>
                        <pre style={{ color: '#CBD5E1' }} className="text-xs whitespace-pre-wrap font-sans leading-relaxed">
                          {selectedJob.cover_letter}
                        </pre>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}