import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  Upload,
  Download,
  Sparkles,
  Loader,
  AlertCircle,
  CheckCircle,
  Eye,
  RefreshCw
} from 'lucide-react';

interface CVRewriterPanelProps {
  onClose?: () => void;
}

export const CVRewriterPanel: React.FC<CVRewriterPanelProps> = ({ onClose }) => {
  const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api/v1';
  
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [profileFile, setProfileFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [latexPreview, setLatexPreview] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  const cvInputRef = useRef<HTMLInputElement>(null);
  const profileInputRef = useRef<HTMLInputElement>(null);

  const handleCVUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setCvFile(file);
      setError(null);
    }
  };

  const handleProfileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setProfileFile(file);
      setError(null);
    }
  };

  const handleRewriteCV = async () => {
    if (!cvFile || !profileFile) {
      setError('Please upload both CV and profile files');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('cv_file', cvFile);
      formData.append('profile_file', profileFile);
      if (jdText) {
        formData.append('jd_text', jdText);
      }

      console.log('🧠 Calling CV rewriter...');
      const response = await fetch(`${API_URL}/cv-rewrite/rewrite`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setLatexPreview(data.latex_content);
      setSuccess('✅ CV rewritten successfully! Preview below.');
      console.log('✓ LaTeX generated:', data.latex_content.length, 'characters');
    } catch (err) {
      console.error('❌ Error:', err);
      setError(err instanceof Error ? err.message : 'Failed to rewrite CV');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!cvFile || !profileFile) {
      setError('Please upload both CV and profile files');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('cv_file', cvFile);
      formData.append('profile_file', profileFile);
      if (jdText) {
        formData.append('jd_text', jdText);
      }

      console.log('📄 Downloading PDF...');
      const response = await fetch(`${API_URL}/cv-rewrite/rewrite-to-pdf`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const blob = await response.blob();
      const url = globalThis.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'resume_rewritten.pdf';
      document.body.appendChild(link);
      link.click();
      link.remove();
      globalThis.URL.revokeObjectURL(url);

      setSuccess('✅ PDF downloaded successfully!');
    } catch (err) {
      console.error('❌ Error downloading PDF:', err);
      setError(err instanceof Error ? err.message : 'Failed to download PDF');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setCvFile(null);
    setProfileFile(null);
    setJdText('');
    setLatexPreview(null);
    setError(null);
    setSuccess(null);
    if (cvInputRef.current) cvInputRef.current.value = '';
    if (profileInputRef.current) profileInputRef.current.value = '';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="space-y-6 p-6 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-lg border border-slate-700"
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <Sparkles className="w-6 h-6 text-amber-400" />
        <h2 className="text-2xl font-bold text-white">CV Rewriter</h2>
        <span className="ml-auto text-xs bg-amber-500 text-black px-2 py-1 rounded font-semibold">
          LLM-Powered
        </span>
      </div>

      <p className="text-slate-400 text-sm">
        Transform your CV using LLM + your profile.md. Get a polished LaTeX resume that exports to PDF.
      </p>

      {/* File Uploads */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* CV Upload */}
        <button
          onClick={() => cvInputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              cvInputRef.current?.click();
            }
          }}
          tabIndex={0}
          className="p-4 border-2 border-dashed border-slate-600 rounded-lg hover:border-blue-500 cursor-pointer transition-colors bg-slate-800/50 text-left"
        >
          <input
            ref={cvInputRef}
            type="file"
            accept=".pdf"
            onChange={handleCVUpload}
            className="hidden"
          />
          <div className="flex flex-col items-center gap-2">
            <Upload className="w-5 h-5 text-slate-400" />
            <div className="text-center">
              <p className="font-semibold text-white text-sm">
                {cvFile ? cvFile.name : 'Upload CV (PDF)'}
              </p>
              <p className="text-xs text-slate-500">Click to select</p>
            </div>
          </div>
        </button>

        {/* Profile Upload */}
        <button
          onClick={() => profileInputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              profileInputRef.current?.click();
            }
          }}
          tabIndex={0}
          className="p-4 border-2 border-dashed border-slate-600 rounded-lg hover:border-green-500 cursor-pointer transition-colors bg-slate-800/50 text-left"
        >
          <input
            ref={profileInputRef}
            type="file"
            accept=".md,.txt"
            onChange={handleProfileUpload}
            className="hidden"
          />
          <div className="flex flex-col items-center gap-2">
            <Upload className="w-5 h-5 text-slate-400" />
            <div className="text-center">
              <p className="font-semibold text-white text-sm">
                {profileFile ? profileFile.name : 'Upload Profile (MD)'}
              </p>
              <p className="text-xs text-slate-500">Click to select</p>
            </div>
          </div>
        </button>
      </div>

      {/* Optional JD */}
      <div>
        <label htmlFor="jd-textarea" className="block text-sm font-semibold text-white mb-2">
          Optional: Job Description (to tailor CV)
        </label>
        <textarea
          id="jd-textarea"
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
          placeholder="Paste job description to tailor your CV to this role..."
          className="w-full h-24 p-3 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Error Alert */}
      {error && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="p-3 bg-red-500/20 border border-red-500 rounded text-red-200 flex items-center gap-2 text-sm"
        >
          <AlertCircle className="w-4 h-4" />
          {error}
        </motion.div>
      )}

      {/* Success Alert */}
      {success && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="p-3 bg-green-500/20 border border-green-500 rounded text-green-200 flex items-center gap-2 text-sm"
        >
          <CheckCircle className="w-4 h-4" />
          {success}
        </motion.div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleRewriteCV}
          disabled={!cvFile || !profileFile || loading}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-semibold rounded transition-colors flex items-center justify-center gap-2"
        >
          {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          Rewrite CV
        </button>

        <button
          onClick={handleDownloadPDF}
          disabled={!cvFile || !profileFile || loading}
          className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white font-semibold rounded transition-colors flex items-center justify-center gap-2"
        >
          {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
          Download PDF
        </button>

        <button
          onClick={handleReset}
          disabled={loading}
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Reset
        </button>
      </div>

      {/* LaTeX Preview */}
      {latexPreview && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-3"
        >
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded transition-colors flex items-center justify-center gap-2"
          >
            <Eye className="w-4 h-4" />
            {showPreview ? 'Hide' : 'Show'} LaTeX Preview
          </button>

          {showPreview && (
            <div className="p-4 bg-slate-900 border border-slate-700 rounded max-h-96 overflow-y-auto font-mono text-xs text-slate-300">
              <pre>{latexPreview.slice(0, 1500)}...</pre>
            </div>
          )}
        </motion.div>
      )}

      {/* Info */}
      <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded text-blue-200 text-xs">
        <p>
          💡 <strong>Tip:</strong> Your CV will be rewritten using LLM to be professional and polished. 
          If you provide a job description, the CV will be tailored to that role.
        </p>
      </div>
    </motion.div>
  );
};
