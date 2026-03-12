import { useState } from 'react';
import { uploadResume, searchJobs, ResumeResponse, JobMatch } from './services/api';
import { Upload, Search, Briefcase, CheckCircle, XCircle, Copy, ExternalLink } from 'lucide-react';

type Step = 'upload' | 'search' | 'results';

function App() {
  const [step, setStep] = useState<Step>('upload');
  const [resume, setResume] = useState<ResumeResponse | null>(null);
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobMatch | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Search form state
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [topK, setTopK] = useState(5);

  // ── Handlers ───────────────────────────────────────────────────────────────

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
    try {
      const result = await searchJobs(resume.resume_id, query, location, remoteOnly, topK);
      setMatches(result.matches);
      setSelectedJob(result.matches[0] || null);
      setStep('results');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Job search failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <Briefcase className="text-blue-600" size={28} />
          <div>
            <h1 className="text-xl font-bold text-gray-900">AI Job Assistant</h1>
            <p className="text-sm text-gray-500">Upload your resume, find your perfect job</p>
          </div>
        </div>
      </header>

      {/* Steps indicator */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="max-w-6xl mx-auto flex gap-8">
          {(['upload', 'search', 'results'] as Step[]).map((s, i) => (
            <div key={s} className={`flex items-center gap-2 text-sm font-medium ${step === s ? 'text-blue-600' : 'text-gray-400'}`}>
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${step === s ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                {i + 1}
              </span>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </div>
          ))}
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-6 py-10">

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Step 1: Upload */}
        {step === 'upload' && (
          <div className="max-w-lg mx-auto">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Your Resume</h2>
            <p className="text-gray-500 mb-8">Upload your PDF resume and let AI find the best matching jobs for you.</p>
            <label className={`block border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${loading ? 'border-blue-300 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'}`}>
              <input type="file" accept=".pdf" onChange={handleFileUpload} className="hidden" disabled={loading} />
              {loading ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  <p className="text-blue-600 font-medium">Parsing your resume with AI...</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <Upload className="text-gray-400" size={40} />
                  <p className="text-gray-600 font-medium">Click to upload PDF resume</p>
                  <p className="text-gray-400 text-sm">Max 10MB</p>
                </div>
              )}
            </label>
          </div>
        )}

        {/* Step 2: Search */}
        {step === 'search' && resume && (
          <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Find Matching Jobs</h2>
            <p className="text-gray-500 mb-6">We parsed your resume. Now let's find the best jobs for you.</p>

            {/* Resume summary */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">✅ Resume Parsed</h3>
              <p className="text-sm text-gray-600 mb-3">{resume.summary}</p>
              <div className="flex flex-wrap gap-2">
                {resume.skills.map(skill => (
                  <span key={skill} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full">{skill}</span>
                ))}
              </div>
            </div>

            {/* Search form */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Job Title / Keywords</label>
                <input
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="e.g. cybersecurity engineer"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={location}
                  onChange={e => setLocation(e.target.value)}
                  placeholder="e.g. India, Remote"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={remoteOnly} onChange={e => setRemoteOnly(e.target.checked)} className="rounded" />
                  Remote only
                </label>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-700">Top</label>
                  <select value={topK} onChange={e => setTopK(Number(e.target.value))} className="border border-gray-300 rounded px-2 py-1 text-sm">
                    {[3, 5, 10].map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                  <label className="text-sm text-gray-700">jobs</label>
                </div>
              </div>
              <button
                onClick={handleSearch}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Searching & generating cover letters...
                  </>
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
              <h2 className="font-bold text-gray-900 text-lg mb-4">Matched Jobs ({matches.length})</h2>
              {matches.map((match) => (
                <div
                  key={match.job.job_id}
                  onClick={() => setSelectedJob(match)}
                  className={`bg-white rounded-xl border p-4 cursor-pointer transition-all ${selectedJob?.job.job_id === match.job.job_id ? 'border-blue-500 shadow-md' : 'border-gray-200 hover:border-gray-300'}`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <h3 className="font-semibold text-gray-900 text-sm leading-tight">{match.job.title}</h3>
                    <span className="text-xs font-bold text-blue-600 ml-2 shrink-0">{Math.round(match.match_score * 100)}%</span>
                  </div>
                  <p className="text-xs text-gray-500">{match.job.company}</p>
                  <p className="text-xs text-gray-400">{match.job.location}</p>
                  {match.job.remote && <span className="mt-2 inline-block px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded-full">Remote</span>}
                </div>
              ))}
              <button
                onClick={() => setStep('search')}
                className="w-full mt-4 border border-gray-300 text-gray-600 py-2 rounded-lg text-sm hover:bg-gray-50"
              >
                ← New Search
              </button>
            </div>

            {/* Job detail */}
            {selectedJob && (
              <div className="col-span-2 space-y-4">
                {/* Job header */}
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">{selectedJob.job.title}</h2>
                      <p className="text-gray-500">{selectedJob.job.company} · {selectedJob.job.location}</p>
                    </div>
                    {selectedJob.job.apply_link && (
                      <a href={selectedJob.job.apply_link} target="_blank" rel="noreferrer"
                        className="flex items-center gap-1 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
                        Apply <ExternalLink size={14} />
                      </a>
                    )}
                  </div>

                  {/* Match reasons */}
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Why you match</h4>
                    <ul className="space-y-1">
                      {selectedJob.match_reasons.map((reason, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                          <CheckCircle size={14} className="text-green-500 mt-0.5 shrink-0" />
                          {reason}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Missing skills */}
                  {selectedJob.missing_skills.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-semibold text-gray-700 mb-2">Skills to develop</h4>
                      <ul className="space-y-1">
                        {selectedJob.missing_skills.map((skill, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
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
                  <div className="bg-white rounded-xl border border-gray-200 p-6">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="font-bold text-gray-900">Generated Cover Letter</h3>
                      <button
                        onClick={() => handleCopy(selectedJob.cover_letter!)}
                        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 border border-gray-300 px-3 py-1.5 rounded-lg"
                      >
                        <Copy size={14} />
                        {copied ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">
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