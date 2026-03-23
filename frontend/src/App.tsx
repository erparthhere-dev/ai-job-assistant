import { useState } from 'react';
import { uploadResume, searchJobs, ResumeResponse, JobMatch } from './services/api';
import { Upload, Search, Briefcase, CheckCircle, XCircle, Copy, ExternalLink, ChevronRight } from 'lucide-react';

type Step = 'upload' | 'search' | 'results';

const PROGRESS_STEPS = [
  { id: 'fetch',    label: 'Fetching jobs from RapidAPI + SerpApi' },
  { id: 'embed',    label: 'Embedding resume & jobs' },
  { id: 'match',    label: 'Scoring job matches' },
  { id: 'analyze',  label: 'Analyzing match reasons' },
  { id: 'letter',   label: 'Generating cover letters' },
];

function getScoreColor(score: number): string {
  if (score >= 0.70) return 'text-green-400';
  if (score >= 0.50) return 'text-yellow-400';
  return 'text-red-400';
}

function getScoreBg(score: number): string {
  if (score >= 0.70) return 'bg-green-400/10 border-green-400/30';
  if (score >= 0.50) return 'bg-yellow-400/10 border-yellow-400/30';
  return 'bg-red-400/10 border-red-400/30';
}

function getScoreLabel(score: number): string {
  if (score >= 0.70) return 'Strong Match';
  if (score >= 0.50) return 'Good Match';
  return 'Weak Match';
}

function App() {
  const [step, setStep] = useState<Step>('upload');
  const [resume, setResume] = useState<ResumeResponse | null>(null);
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobMatch | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [progressStep, setProgressStep] = useState(-1);

  // Search form
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

    // Simulate progress steps
    const progressInterval = setInterval(() => {
      setProgressStep(prev => {
        if (prev >= PROGRESS_STEPS.length - 1) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + 1;
      });
    }, 3000);

    try {
      const result = await searchJobs(resume.resume_id, query, location, remoteOnly, topK);
      clearInterval(progressInterval);
      setProgressStep(PROGRESS_STEPS.length);
      setMatches(result.matches);
      setSelectedJob(result.matches[0] || null);
      setStep('results');
    } catch (err: any) {
      clearInterval(progressInterval);
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
    <div className="min-h-screen bg-gray-950 text-gray-100">

      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 bg-gray-900">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center">
            <Briefcase size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">AI Job Assistant</h1>
            <p className="text-xs text-gray-400">Powered by GPT-4o + LangGraph</p>
          </div>
        </div>
      </header>

      {/* Step indicator */}
      <div className="border-b border-gray-800 bg-gray-900 px-6 py-3">
        <div className="max-w-6xl mx-auto flex items-center gap-2">
          {(['upload', 'search', 'results'] as Step[]).map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`flex items-center gap-2 text-sm font-medium px-3 py-1 rounded-full transition-all ${step === s ? 'bg-blue-600/20 text-blue-400' : 'text-gray-500'}`}>
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${step === s ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400'}`}>
                  {i + 1}
                </span>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </div>
              {i < 2 && <ChevronRight size={14} className="text-gray-600" />}
            </div>
          ))}
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-6 py-10">

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Step 1: Upload */}
        {step === 'upload' && (
          <div className="max-w-lg mx-auto">
            <h2 className="text-3xl font-bold text-white mb-2">Upload Your Resume</h2>
            <p className="text-gray-400 mb-8">Let AI find the best matching jobs and write personalized cover letters for you.</p>
            <label className={`block border-2 border-dashed rounded-2xl p-14 text-center cursor-pointer transition-all ${loading ? 'border-blue-500/50 bg-blue-500/5' : 'border-gray-700 hover:border-blue-500/50 hover:bg-blue-500/5'}`}>
              <input type="file" accept=".pdf" onChange={handleFileUpload} className="hidden" disabled={loading} />
              {loading ? (
                <div className="flex flex-col items-center gap-4">
                  <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  <p className="text-blue-400 font-medium">Parsing your resume with AI...</p>
                  <p className="text-gray-500 text-sm">Extracting skills, experience and education</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-4">
                  <div className="w-16 h-16 bg-gray-800 rounded-2xl flex items-center justify-center">
                    <Upload className="text-blue-400" size={32} />
                  </div>
                  <div>
                    <p className="text-white font-semibold text-lg">Click to upload PDF resume</p>
                    <p className="text-gray-500 text-sm mt-1">Max 10MB · PDF only</p>
                  </div>
                </div>
              )}
            </label>
          </div>
        )}

        {/* Step 2: Search */}
        {step === 'search' && resume && (
          <div className="max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold text-white mb-2">Find Matching Jobs</h2>
            <p className="text-gray-400 mb-6">Resume parsed successfully. Now let's find the best jobs for you.</p>

            {/* Resume summary card */}
            <div className="bg-gray-900 rounded-2xl border border-gray-800 p-5 mb-6">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle size={16} className="text-green-400" />
                <h3 className="font-semibold text-white text-sm">Resume Parsed</h3>
                <span className="ml-auto text-xs text-gray-500">{resume.skills.length} skills found</span>
              </div>
              <p className="text-sm text-gray-400 mb-4 leading-relaxed">{resume.summary}</p>
              <div className="flex flex-wrap gap-2">
                {resume.skills.slice(0, 12).map(skill => (
                  <span key={skill} className="px-2.5 py-1 bg-blue-600/10 text-blue-400 text-xs rounded-full border border-blue-600/20">
                    {skill}
                  </span>
                ))}
                {resume.skills.length > 12 && (
                  <span className="px-2.5 py-1 bg-gray-800 text-gray-400 text-xs rounded-full">
                    +{resume.skills.length - 12} more
                  </span>
                )}
              </div>
            </div>

            {/* Search form */}
            <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Job Title / Keywords</label>
                <input
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="e.g. cybersecurity engineer"
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Location</label>
                <input
                  type="text"
                  value={location}
                  onChange={e => setLocation(e.target.value)}
                  placeholder="e.g. India, Remote"
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                  <input type="checkbox" checked={remoteOnly} onChange={e => setRemoteOnly(e.target.checked)} className="rounded accent-blue-500" />
                  Remote only
                </label>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-300">Top</label>
                  <select value={topK} onChange={e => setTopK(Number(e.target.value))} className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                    {[3, 5, 10].map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                  <label className="text-sm text-gray-300">results</label>
                </div>
              </div>

              {/* Progress bar */}
              {loading && progressStep >= 0 && (
                <div className="bg-gray-800 rounded-xl p-4 space-y-2">
                  {PROGRESS_STEPS.map((ps, i) => (
                    <div key={ps.id} className="flex items-center gap-3">
                      {i < progressStep ? (
                        <CheckCircle size={14} className="text-green-400 shrink-0" />
                      ) : i === progressStep ? (
                        <div className="w-3.5 h-3.5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin shrink-0" />
                      ) : (
                        <div className="w-3.5 h-3.5 rounded-full border border-gray-600 shrink-0" />
                      )}
                      <span className={`text-xs ${i < progressStep ? 'text-green-400' : i === progressStep ? 'text-blue-400' : 'text-gray-600'}`}>
                        {ps.label}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={handleSearch}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <span className="text-sm">Processing...</span>
                ) : (
                  <>
                    <Search size={16} />
                    Find Matching Jobs
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Results */}
        {step === 'results' && (
          <div className="grid grid-cols-3 gap-6">

            {/* Job list */}
            <div className="col-span-1 space-y-3">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-white">Matches ({matches.length})</h2>
                <button onClick={() => setStep('search')} className="text-xs text-gray-400 hover:text-white transition-colors">
                  ← New Search
                </button>
              </div>
              {matches.map((match) => (
                <div
                  key={match.job.job_id}
                  onClick={() => setSelectedJob(match)}
                  className={`bg-gray-900 rounded-xl border p-4 cursor-pointer transition-all hover:border-gray-600 ${selectedJob?.job.job_id === match.job.job_id ? 'border-blue-500/50 bg-blue-500/5' : 'border-gray-800'}`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium text-white text-sm leading-tight pr-2">{match.job.title}</h3>
                    <span className={`text-xs font-bold shrink-0 ${getScoreColor(match.match_score)}`}>
                      {Math.round(match.match_score * 100)}%
                    </span>
                  </div>
                  <p className="text-xs text-gray-400">{match.job.company}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{match.job.location}</p>
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${getScoreBg(match.match_score)} ${getScoreColor(match.match_score)}`}>
                      {getScoreLabel(match.match_score)}
                    </span>
                    {match.job.remote && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-purple-400/10 border border-purple-400/30 text-purple-400">
                        Remote
                      </span>
                    )}
                    {match.job.source && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-700 border border-gray-600 text-gray-300">
                        {match.job.source}
                      </span>
                    )}
                  </div>

                </div>
              ))}

            </div>

            {/* Job detail */}
            {selectedJob && (
              <div className="col-span-2 space-y-4">

                {/* Job header */}
                <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h2 className="text-xl font-bold text-white">{selectedJob.job.title}</h2>
                      <p className="text-gray-400 mt-1">
                        {selectedJob.job.company} · {selectedJob.job.location}
                        {selectedJob.job.source && (
                          <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-gray-700 border border-gray-600 text-gray-300">
                            {selectedJob.job.source}
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <div className={`text-center px-4 py-2 rounded-xl border ${getScoreBg(selectedJob.match_score)}`}>
                        <div className={`text-2xl font-bold ${getScoreColor(selectedJob.match_score)}`}>
                          {Math.round(selectedJob.match_score * 100)}%
                        </div>
                        <div className={`text-xs ${getScoreColor(selectedJob.match_score)}`}>
                          {getScoreLabel(selectedJob.match_score)}
                        </div>
                      </div>
                      {selectedJob.job.apply_link && (
  
                          <a href={selectedJob.job.apply_link}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors"
                        >
                          Apply <ExternalLink size={13} />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Match reasons */}
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-gray-300 mb-3">Why you match</h4>
                    <ul className="space-y-2">
                      {selectedJob.match_reasons.map((reason, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-sm text-gray-300">
                          <CheckCircle size={14} className="text-green-400 mt-0.5 shrink-0" />
                          {reason}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Missing skills */}
                  {selectedJob.missing_skills.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-300 mb-3">Skills to develop</h4>
                      <ul className="space-y-2">
                        {selectedJob.missing_skills.map((skill, i) => (
                          <li key={i} className="flex items-start gap-2.5 text-sm text-gray-300">
                            <XCircle size={14} className="text-red-400 mt-0.5 shrink-0" />
                            {skill}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Cover letter */}
                {selectedJob.cover_letter && (
                  <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="font-bold text-white">Generated Cover Letter</h3>
                      <button
                        onClick={() => handleCopy(selectedJob.cover_letter!)}
                        className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white border border-gray-700 hover:border-gray-500 px-3 py-1.5 rounded-lg transition-all"
                      >
                        <Copy size={13} />
                        {copied ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                    <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
                      {selectedJob.cover_letter}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;