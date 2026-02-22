import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  Zap,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  FileCode,
  Trash2
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

import { semanticMatch, semanticMatchSmart, optimizeCV, generateFullReport } from '../services/api';
import {
  SemanticMatchResult,
  CVOptimizationResult,
  SemanticCVReport
} from '../types';
import { GapAnalysisView } from './GapAnalysisView';

interface SemanticMatchingPanelProps {
  onClose?: () => void;
}

export const SemanticMatchingPanel: React.FC<SemanticMatchingPanelProps> = ({
  onClose
}) => {
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [profileFile, setProfileFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'match' | 'optimize' | 'full'>('match');
  const [useSmart, setUseSmart] = useState(true); // Default to smart matching
  
  const [matchResult, setMatchResult] = useState<SemanticMatchResult | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<
    CVOptimizationResult | null
  >(null);
  const [fullReport, setFullReport] = useState<SemanticCVReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cvInputRef = useRef<HTMLInputElement>(null);
  const profileInputRef = useRef<HTMLInputElement>(null);

  const handleCVFileSelect = (files: FileList | null) => {
    if (files && files[0]) {
      if (files[0].type !== 'application/pdf') {
        setError('Please select a PDF file for CV');
        return;
      }
      setCvFile(files[0]);
      setError(null);
    }
  };

  const handleProfileFileSelect = (files: FileList | null) => {
    if (files && files[0]) {
      if (!files[0].type.includes('text') && files[0].type !== 'application/octet-stream') {
        setError('Please select a markdown or text file for profile');
        return;
      }
      setProfileFile(files[0]);
      setError(null);
    }
  };

  const handleMatch = async () => {
    if (!cvFile || !jdText.trim()) {
      setError('Please provide both CV file and job description');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = useSmart 
        ? await semanticMatchSmart(cvFile, jdText, profileFile)
        : await semanticMatch(cvFile, jdText, profileFile);
      setMatchResult(result);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async () => {
    if (!cvFile || !jdText.trim()) {
      setError('Please provide both CV file and job description');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await optimizeCV(cvFile, jdText, profileFile);
      setOptimizationResult(result);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleFullReport = async () => {
    if (!cvFile || !jdText.trim()) {
      setError('Please provide both CV file and job description');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await generateFullReport(
        cvFile,
        jdText,
        profileFile,
        true
      );
      setFullReport(result);
      setMatchResult(result.matching_result);
      setOptimizationResult(result.optimization_result);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setCvFile(null);
    setProfileFile(null);
    setJdText('');
    setMatchResult(null);
    setOptimizationResult(null);
    setFullReport(null);
    setError(null);
  };

  const scoreData = matchResult
    ? [
        {
          name: 'Match',
          value: Math.round(matchResult.overall_score * 100)
        },
        {
          name: 'Skill Ratio',
          value: Math.round(matchResult.skill_match_ratio * 100)
        }
      ]
    : [];

  const improvementData = optimizationResult
    ? [
        {
          name: 'Before',
          score: Math.round(optimizationResult.original_score * 100)
        },
        {
          name: 'After',
          score: Math.round(optimizationResult.optimized_score * 100)
        }
      ]
    : [];

  const getConfidenceColor = (confidence: string) => {
    const colors: Record<string, string> = {
      strong: '#00ff9d',
      viable: '#ffa500',
      risky: '#ff6b6b',
      low: '#ff0000'
    };
    return colors[confidence] || '#00ff9d';
  };

  const getScoreGradient = (score: number) => {
    if (score >= 0.75) return 'from-green-500 to-emerald-600';
    if (score >= 0.6) return 'from-yellow-500 to-amber-600';
    if (score >= 0.45) return 'from-orange-500 to-red-600';
    return 'from-red-500 to-red-700';
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
          Semantic CV Matching
        </h1>
        <p className="text-gray-400">
          Analyze CV-JD alignment and optimize your resume
        </p>
      </motion.div>

      {/* Input Section */}
      {!matchResult && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-gray-900/50 border border-cyan-500/20 rounded-lg p-6 space-y-4 backdrop-blur"
        >
          {/* File Upload Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* CV Upload */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="relative group"
            >
              <div
                onClick={() => cvInputRef.current?.click()}
                className="cursor-pointer p-4 border-2 border-dashed border-cyan-500/50 rounded-lg hover:border-cyan-400 transition-colors bg-cyan-900/10 hover:bg-cyan-900/20"
              >
                <input
                  ref={cvInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleCVFileSelect(e.target.files)}
                  className="hidden"
                />
                <div className="flex items-center justify-center gap-2 text-cyan-300">
                  <Upload size={20} />
                  <span>
                    {cvFile ? cvFile.name : 'Upload CV (PDF)'}
                  </span>
                </div>
              </div>
            </motion.div>

            {/* Profile Upload (Optional) */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="relative group"
            >
              <div
                onClick={() => profileInputRef.current?.click()}
                className="cursor-pointer p-4 border-2 border-dashed border-purple-500/50 rounded-lg hover:border-purple-400 transition-colors bg-purple-900/10 hover:bg-purple-900/20"
              >
                <input
                  ref={profileInputRef}
                  type="file"
                  accept=".md,.txt"
                  onChange={(e) => handleProfileFileSelect(e.target.files)}
                  className="hidden"
                />
                <div className="flex items-center justify-center gap-2 text-purple-300">
                  <FileText size={20} />
                  <span>
                    {profileFile ? profileFile.name : 'Profile (Optional)'}
                  </span>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Job Description */}
          <div>
            <label className="text-sm font-semibold text-gray-300 mb-2 block">
              Job Description
            </label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the job description here..."
              className="w-full h-32 bg-gray-800/50 border border-gray-700 rounded-lg p-3 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50"
            />
          </div>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-900/30 border border-red-500/50 rounded-lg p-3 flex items-start gap-2 text-red-200"
            >
              <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </motion.div>
          )}

          {/* Smart Mode Toggle */}
          <div className="flex items-center justify-between bg-gradient-to-r from-cyan-900/20 to-blue-900/20 border border-cyan-500/30 rounded-lg p-4">
            <div>
              <p className="font-semibold text-cyan-300">Smart LLM-Powered Matching</p>
              <p className="text-xs text-gray-400 mt-1">
                {useSmart 
                  ? '✅ Enabled - Uses AI to parse requirements for better results'
                  : '❌ Disabled - Uses simple fragmentation'}
              </p>
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useSmart}
                onChange={(e) => setUseSmart(e.target.checked)}
                className="w-5 h-5"
              />
              <span className="text-cyan-300 font-medium">{useSmart ? 'ON' : 'OFF'}</span>
            </label>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 flex-wrap">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleMatch}
              disabled={loading || !cvFile || !jdText.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg font-semibold text-white hover:shadow-lg hover:shadow-cyan-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <Zap size={18} />
              Match CV to JD
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleOptimize}
              disabled={loading || !cvFile || !jdText.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg font-semibold text-white hover:shadow-lg hover:shadow-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <TrendingUp size={18} />
              Optimize CV
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleFullReport}
              disabled={loading || !cvFile || !jdText.trim()}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg font-semibold text-white hover:shadow-lg hover:shadow-green-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <FileCode size={18} />
              Full Report
            </motion.button>

            {(cvFile || jdText) && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleReset}
                className="flex items-center gap-2 px-4 py-2 bg-gray-700 rounded-lg font-semibold text-white hover:bg-gray-600 transition-all"
              >
                <Trash2 size={18} />
                Reset
              </motion.button>
            )}
          </div>

          {loading && (
            <div className="flex items-center justify-center gap-2 text-cyan-400">
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
              <span>Processing your request...</span>
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
            </div>
          )}
        </motion.div>
      )}

      {/* Results Section */}
      <AnimatePresence>
        {matchResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-4"
          >
            {/* Score Card */}
            <motion.div
              className={`bg-gradient-to-br ${getScoreGradient(
                matchResult.overall_score
              )}/10 border border-cyan-500/30 rounded-lg p-6 backdrop-blur`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-cyan-300 mb-2">
                    Overall Match Score
                  </h2>
                  <p className="text-4xl font-bold text-white">
                    {Math.round(matchResult.overall_score * 100)}%
                  </p>
                  <p
                    className="text-sm font-semibold mt-2 uppercase tracking-wider"
                    style={{ color: getConfidenceColor(matchResult.confidence) }}
                  >
                    {matchResult.confidence}
                  </p>
                </div>

                {scoreData.length > 0 && (
                  <ResponsiveContainer width={200} height={120}>
                    <BarChart data={scoreData}>
                      <XAxis dataKey="name" stroke="#888" />
                      <YAxis stroke="#888" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1a1a2e',
                          border: '1px solid #00ff9d'
                        }}
                        formatter={(value) => `${value}%`}
                      />
                      <Bar dataKey="value" fill="#00ff9d" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </motion.div>

            {/* Recommendations */}
            {matchResult.recommendations.length > 0 && (
              <motion.div className="bg-gray-900/50 border border-cyan-500/20 rounded-lg p-4 backdrop-blur">
                <h3 className="text-sm font-semibold text-cyan-300 mb-3">
                  Recommendations
                </h3>
                <ul className="space-y-2">
                  {matchResult.recommendations.map((rec, i) => (
                    <motion.li
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="flex items-start gap-2 text-gray-300 text-sm"
                    >
                      <CheckCircle size={16} className="flex-shrink-0 mt-0.5 text-green-400" />
                      <span>{rec}</span>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            )}

            {/* Gap Analysis */}
            {matchResult.gaps.length > 0 && (
              <GapAnalysisView gaps={matchResult.gaps} />
            )}

            {/* Optimization Results */}
            {optimizationResult && (
              <motion.div className="bg-gray-900/50 border border-purple-500/20 rounded-lg p-6 backdrop-blur">
                <h3 className="text-lg font-semibold text-purple-300 mb-4">
                  Optimization Results
                </h3>

                {improvementData.length > 0 && (
                  <div className="mb-6">
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={improvementData}>
                        <XAxis dataKey="name" stroke="#888" />
                        <YAxis stroke="#888" />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#1a1a2e',
                            border: '1px solid #a855f7'
                          }}
                          formatter={(value) => `${value}%`}
                        />
                        <Bar dataKey="score" fill="#a855f7" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-gray-800/50 rounded p-3">
                    <p className="text-xs text-gray-400 mb-1">Original</p>
                    <p className="text-2xl font-bold text-purple-300">
                      {Math.round(optimizationResult.original_score * 100)}%
                    </p>
                  </div>
                  <div className="bg-gray-800/50 rounded p-3">
                    <p className="text-xs text-gray-400 mb-1">Optimized</p>
                    <p className="text-2xl font-bold text-green-400">
                      {Math.round(optimizationResult.optimized_score * 100)}%
                    </p>
                  </div>
                  <div className="bg-gray-800/50 rounded p-3">
                    <p className="text-xs text-gray-400 mb-1">Improvement</p>
                    <p className="text-2xl font-bold text-cyan-400">
                      +{Math.round(optimizationResult.improvement_delta * 100)}%
                    </p>
                  </div>
                </div>

                {optimizationResult.improvements_made.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-semibold text-gray-300">
                      Improvements Made:
                    </p>
                    <ul className="space-y-1">
                      {optimizationResult.improvements_made.map((imp, i) => (
                        <li key={i} className="text-sm text-gray-400 flex items-start gap-2">
                          <CheckCircle size={14} className="flex-shrink-0 mt-0.5 text-green-400" />
                          <span>{imp}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 justify-center">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  setMatchResult(null);
                  setOptimizationResult(null);
                  setFullReport(null);
                }}
                className="px-6 py-2 bg-gray-700 rounded-lg font-semibold text-white hover:bg-gray-600 transition-all"
              >
                Back to Input
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
