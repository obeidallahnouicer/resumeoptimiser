import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Cpu, 
  Download, 
  RefreshCcw, 
  ShieldCheck, 
  Zap, 
  Code, 
  Layers, 
  Briefcase,
  Upload,
  FileText,
  Trash2,
  FileCode
} from 'lucide-react';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell
} from 'recharts';

import { generateCV, downloadPDF } from './services/api';
import { GenerationResponse } from './types';
import { GlitchText } from './components/GlitchText';
import { ScoreGauge } from './components/ScoreGauge';
import { TerminalLog } from './components/TerminalLog';

// --- Background Component ---
const CyberBackground = () => (
  <div className="fixed inset-0 pointer-events-none z-0">
    <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_#111119_0%,_#050505_100%)]"></div>
    {/* Grid Floor */}
    <div 
      className="absolute bottom-0 w-full h-1/2 opacity-20"
      style={{
        background: `linear-gradient(transparent 0%, #00ff9d 100%), 
                     linear-gradient(90deg, rgba(0,255,157,0.1) 1px, transparent 1px),
                     linear-gradient(0deg, rgba(0,255,157,0.1) 1px, transparent 1px)`,
        backgroundSize: '100% 100%, 40px 40px, 40px 40px',
        transform: 'perspective(500px) rotateX(60deg) translateY(100px)'
      }}
    ></div>
  </div>
);

function App() {
  const [jdText, setJdText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<GenerationResponse | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (!jdText.trim()) return;
    
    setLoading(true);
    setData(null);

    const result = await generateCV(jdText, file);
    setData(result);
    setLoading(false);
  };

  const handleReset = () => {
    setData(null);
    setJdText('');
    setFile(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
    } else if (droppedFile) {
        alert("INVALID_FORMAT: PDF_REQUIRED");
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  // Prepare Chart Data
  const radarData = data ? [
    { subject: 'Stack', A: data.cv_score.breakdown.stack_alignment, fullMark: 40 },
    { subject: 'Capability', A: data.cv_score.breakdown.capability_match, fullMark: 20 },
    { subject: 'Seniority', A: data.cv_score.breakdown.seniority_fit, fullMark: 15 },
    { subject: 'Domain', A: data.cv_score.breakdown.domain_relevance, fullMark: 10 },
    { subject: 'Sponsor', A: data.cv_score.breakdown.sponsorship_feasibility, fullMark: 15 },
  ] : [];

  return (
    <div className="relative min-h-screen text-gray-200 font-sans selection:bg-cyber-green selection:text-black">
      <CyberBackground />

      <main className="relative z-10 container mx-auto px-4 py-8 md:py-12 max-w-7xl">
        
        {/* Header */}
        <header className="flex justify-between items-center mb-12 border-b border-gray-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyber-green/10 border border-cyber-green rounded">
              <Cpu className="text-cyber-green" size={24} />
            </div>
            <div>
                <GlitchText text="RESUME//OPTIMISER_V2" as="h1" className="text-2xl md:text-3xl font-display font-bold tracking-wider text-white" />
                <p className="text-xs text-cyber-green font-mono uppercase tracking-[0.3em]">System Online</p>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-4 text-xs font-mono text-gray-500">
             <span>MEM: 64TB</span>
             <span>NET: SECURE</span>
             <span className="animate-pulse text-cyber-green">● LIVE</span>
          </div>
        </header>

        <AnimatePresence mode="wait">
          {!data && !loading ? (
            /* --- INPUT VIEW --- */
            <motion.div 
              key="input"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-5xl mx-auto"
            >
              <div className="bg-cyber-black/80 backdrop-blur-md border border-gray-800 rounded-xl p-1 shadow-[0_0_50px_rgba(0,255,157,0.05)]">
                <div className="bg-cyber-dark/50 rounded-lg border border-gray-800 p-6 md:p-8">
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    
                    {/* LEFT COLUMN: PDF UPLOAD */}
                    <div className="flex flex-col h-full">
                        <label className="flex items-center gap-2 text-cyber-green font-mono mb-4 text-sm">
                            <FileText size={16} />
                            <span>UPLOAD_SOURCE_CV (PDF)</span>
                        </label>
                        
                        <div 
                            className={`flex-1 min-h-[250px] border-2 border-dashed rounded-lg transition-all duration-300 flex flex-col items-center justify-center cursor-pointer relative overflow-hidden ${
                                isDragging 
                                ? 'border-cyber-green bg-cyber-green/10 scale-[1.02]' 
                                : file 
                                    ? 'border-cyber-cyan bg-cyber-cyan/5' 
                                    : 'border-gray-700 hover:border-gray-500 hover:bg-gray-800/50'
                            }`}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() => !file && fileInputRef.current?.click()}
                        >
                            <input 
                                type="file" 
                                ref={fileInputRef}
                                className="hidden" 
                                accept="application/pdf"
                                onChange={handleFileSelect}
                            />
                            
                            {file ? (
                                <div className="z-10 text-center p-4">
                                    <div className="w-16 h-16 bg-cyber-cyan/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-cyber-cyan">
                                        <FileText className="text-cyber-cyan" size={32} />
                                    </div>
                                    <p className="font-mono text-cyber-cyan text-sm break-all max-w-[200px]">{file.name}</p>
                                    <p className="text-xs text-gray-500 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                                    
                                    <button 
                                        onClick={(e) => { e.stopPropagation(); setFile(null); }}
                                        className="mt-4 flex items-center gap-2 text-xs text-cyber-pink hover:text-white transition-colors mx-auto"
                                    >
                                        <Trash2 size={12} /> REMOVE_FILE
                                    </button>
                                </div>
                            ) : (
                                <div className="z-10 text-center p-4">
                                    <Upload className={`mx-auto mb-4 transition-all duration-500 ${isDragging ? 'text-cyber-green scale-110' : 'text-gray-600'}`} size={40} />
                                    <p className="font-display font-bold text-lg text-gray-300">DROP PDF HERE</p>
                                    <p className="font-mono text-xs text-gray-600 mt-2">OR CLICK TO BROWSE</p>
                                </div>
                            )}

                            {/* Scanline effect for drag area */}
                            {isDragging && (
                                <div className="absolute inset-0 bg-[linear-gradient(transparent_0%,_rgba(0,255,157,0.1)_50%,_transparent_100%)] bg-[length:100%_20px] animate-scanline pointer-events-none"></div>
                            )}
                        </div>
                    </div>

                    {/* RIGHT COLUMN: JD INPUT */}
                    <div className="flex flex-col h-full">
                        <label className="flex items-center gap-2 text-cyber-green font-mono mb-4 text-sm">
                            <Code size={16} />
                            <span>INPUT_JOB_DESCRIPTION_STREAM</span>
                        </label>
                        <textarea
                            value={jdText}
                            onChange={(e) => setJdText(e.target.value)}
                            placeholder="PASTE TARGET JD CONTENT..."
                            className="flex-1 min-h-[250px] w-full bg-black/50 border border-gray-700 rounded p-4 font-mono text-sm text-gray-300 focus:border-cyber-green focus:ring-1 focus:ring-cyber-green focus:outline-none resize-none transition-all placeholder:text-gray-700"
                        />
                    </div>

                  </div>

                  <div className="mt-8 flex justify-end">
                    <button
                      onClick={handleSubmit}
                      disabled={!jdText.trim()}
                      className="group relative px-8 py-3 bg-cyber-green/10 border border-cyber-green/50 hover:bg-cyber-green hover:text-black transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed w-full md:w-auto"
                    >
                      <span className="font-display font-bold tracking-widest text-lg">INITIATE_OPTIMISATION</span>
                      <div className="absolute inset-0 border border-white/0 group-hover:border-white/20 scale-105 opacity-0 group-hover:opacity-100 transition-all duration-500 rounded-sm"></div>
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-center opacity-50">
                <div className="flex flex-col items-center gap-2">
                    <ShieldCheck className="text-cyber-green" />
                    <h3 className="font-mono text-sm text-cyber-green">NO HALLUCINATIONS</h3>
                    <p className="text-xs text-gray-500">Truth-file constraint logic</p>
                </div>
                <div className="flex flex-col items-center gap-2">
                    <Zap className="text-cyber-cyan" />
                    <h3 className="font-mono text-sm text-cyber-cyan">LATEX ENGINE</h3>
                    <p className="text-xs text-gray-500">High-fidelity compilation</p>
                </div>
                <div className="flex flex-col items-center gap-2">
                    <Layers className="text-cyber-pink" />
                    <h3 className="font-mono text-sm text-cyber-pink">MULTI-FACTOR SCORING</h3>
                    <p className="text-xs text-gray-500">5-dimensional analysis</p>
                </div>
              </div>
            </motion.div>

          ) : loading ? (
            /* --- LOADING VIEW --- */
            <motion.div 
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center h-[60vh]"
            >
              <div className="relative">
                <div className="w-24 h-24 border-4 border-cyber-green/30 border-t-cyber-green rounded-full animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                    <Cpu className="text-cyber-green animate-pulse" />
                </div>
              </div>
              <h2 className="mt-8 font-display text-2xl animate-pulse text-white">PROCESSING_DATA_STREAMS</h2>
              <div className="mt-2 font-mono text-cyber-cyan text-sm">
                 {file ? "Extracting PDF Data..." : "Loading Truth File..."} Parsing JD... Optimizing...
              </div>
            </motion.div>

          ) : (
            /* --- DASHBOARD VIEW --- */
            <motion.div 
              key="dashboard"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-6"
            >
              
              {/* Top Left: Score */}
              <div className="lg:col-span-4 bg-cyber-black/80 border border-gray-800 rounded-xl p-6 flex flex-col items-center justify-center relative overflow-hidden group">
                 <div className="absolute top-0 right-0 p-2 opacity-50">
                    <Layers size={16} className="text-gray-500" />
                 </div>
                 <ScoreGauge score={data!.cv_score.total_score} />
                 <div className={`mt-4 px-3 py-1 rounded border text-xs font-bold tracking-widest ${
                    data!.cv_score.category === 'green' ? 'border-green-500 text-green-500 bg-green-500/10' :
                    data!.cv_score.category === 'yellow' ? 'border-yellow-500 text-yellow-500 bg-yellow-500/10' :
                    'border-red-500 text-red-500 bg-red-500/10'
                 }`}>
                    STATUS: {data!.cv_score.category.toUpperCase()}
                 </div>
              </div>

              {/* Top Center: Parsed Info */}
              <div className="lg:col-span-5 bg-cyber-black/80 border border-gray-800 rounded-xl p-6 relative overflow-hidden">
                <h3 className="text-cyber-green font-mono text-sm mb-4 border-b border-gray-800 pb-2 flex items-center gap-2">
                    <Briefcase size={14} /> MISSION_PARAMETERS
                </h3>
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <span className="text-xs text-gray-500 block mb-1">SENIORITY</span>
                        <span className="text-lg font-display text-white">{data!.parsed_jd.seniority}</span>
                    </div>
                    <div>
                        <span className="text-xs text-gray-500 block mb-1">DOMAIN</span>
                        <div className="flex flex-wrap gap-1">
                            {data!.parsed_jd.domain.slice(0, 3).map(k => (
                                <span key={k} className="text-xs bg-gray-800 text-gray-300 px-1 rounded">{k}</span>
                            ))}
                        </div>
                    </div>
                    <div className="col-span-2">
                        <span className="text-xs text-gray-500 block mb-1">REQUIRED_STACK</span>
                        <div className="flex flex-wrap gap-2">
                            {data!.parsed_jd.core_stack.slice(0, 8).map(tech => (
                                <span key={tech} className="px-2 py-1 bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan text-xs rounded-sm font-mono">
                                    {tech}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
              </div>

              {/* Top Right: Actions */}
              <div className="lg:col-span-3 flex flex-col gap-4">
                <button 
                  onClick={() => downloadPDF(data!.pdf_path)}
                  className="flex-1 bg-cyber-green text-black font-bold font-display text-xl rounded-xl flex items-center justify-center gap-2 hover:bg-white transition-colors shadow-[0_0_20px_rgba(0,255,157,0.3)]"
                >
                    <Download /> DOWNLOAD_PDF
                </button>
                <button 
                  onClick={handleReset}
                  className="h-16 border border-gray-700 hover:border-white text-gray-400 hover:text-white rounded-xl flex items-center justify-center gap-2 transition-all"
                >
                    <RefreshCcw size={18} /> NEW_OPERATION
                </button>
              </div>

              {/* Middle: Charts */}
              <div className="lg:col-span-8 bg-cyber-black/80 border border-gray-800 rounded-xl p-6 min-h-[300px]">
                 <h3 className="text-cyber-green font-mono text-sm mb-4">SCORING_MATRIX_BREAKDOWN</h3>
                 <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={radarData} layout="vertical" margin={{ left: 20 }}>
                        <XAxis type="number" hide />
                        <YAxis dataKey="subject" type="category" stroke="#6b7280" tick={{fontSize: 12, fontFamily: 'monospace'}} width={80} />
                        <Tooltip 
                            contentStyle={{ backgroundColor: '#050505', borderColor: '#374151', color: '#fff' }} 
                            itemStyle={{ color: '#00ff9d' }}
                            cursor={{fill: 'rgba(255,255,255,0.05)'}}
                        />
                        <Bar dataKey="A" barSize={20} radius={[0, 4, 4, 0]}>
                            {radarData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.A / entry.fullMark > 0.8 ? '#00ff9d' : entry.A / entry.fullMark > 0.5 ? '#fbbf24' : '#ef4444'} />
                            ))}
                        </Bar>
                    </BarChart>
                 </ResponsiveContainer>
              </div>

              <div className="lg:col-span-4 bg-cyber-black/80 border border-gray-800 rounded-xl p-6 min-h-[300px]">
                 <h3 className="text-cyber-green font-mono text-sm mb-4">SKILL_COVERAGE</h3>
                 <ResponsiveContainer width="100%" height={250}>
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                        <PolarGrid stroke="#374151" />
                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                        <PolarRadiusAxis angle={30} domain={[0, 40]} tick={false} axisLine={false} />
                        <Radar name="Score" dataKey="A" stroke="#00ff9d" strokeWidth={2} fill="#00ff9d" fillOpacity={0.3} />
                        <Tooltip contentStyle={{ backgroundColor: '#050505', borderColor: '#374151' }} />
                    </RadarChart>
                 </ResponsiveContainer>
              </div>

               {/* Bottom Left: Skills List */}
               <div className="lg:col-span-4 bg-cyber-black/80 border border-gray-800 rounded-xl p-6">
                    <h3 className="text-cyber-green font-mono text-sm mb-4 flex justify-between">
                        <span>SKILL_ANALYSIS</span>
                        <span className="text-xs text-gray-500">{Math.round((data!.skill_match.total_matched / data!.skill_match.total_jd_requirements) * 100)}% MATCH</span>
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <span className="text-xs text-cyber-green block mb-2 font-bold">DIRECT MATCHES</span>
                            <div className="flex flex-wrap gap-2">
                                {Object.entries(data!.skill_match.matches)
                                    .filter(([_, match]) => (match as any).status === 'direct')
                                    .length ? Object.entries(data!.skill_match.matches)
                                        .filter(([_, match]) => (match as any).status === 'direct')
                                        .map(([skill]) => (
                                    <span key={skill} className="px-2 py-1 bg-cyber-green/20 text-cyber-green text-xs rounded border border-cyber-green/20">{skill}</span>
                                )) : <span className="text-gray-600 text-xs italic">None detected</span>}
                            </div>
                        </div>
                        <div>
                            <span className="text-xs text-cyber-cyan block mb-2 font-bold">MISSING REQUIREMENTS</span>
                            <div className="flex flex-wrap gap-2">
                                {data!.skill_match.unmatched_jd_requirements.length ? data!.skill_match.unmatched_jd_requirements.map(s => (
                                    <span key={s} className="px-2 py-1 bg-cyber-pink/20 text-cyber-pink text-xs rounded border border-cyber-pink/20 line-through decoration-cyber-pink/50">{s}</span>
                                )) : <span className="text-gray-600 text-xs italic">No gaps found</span>}
                            </div>
                        </div>
                    </div>
               </div>
               
               {/* Bottom Center: Latex Preview (The "See Optimized CV" part) */}
               <div className="lg:col-span-5 bg-cyber-black/80 border border-gray-800 rounded-xl p-6 flex flex-col">
                  <h3 className="text-cyber-cyan font-mono text-sm mb-4 flex items-center gap-2">
                     <FileCode size={14} /> GENERATED_SOURCE_CODE
                  </h3>
                  <div className="flex-1 bg-black/50 rounded border border-gray-800 p-4 overflow-hidden relative group">
                      <pre className="text-[10px] text-gray-400 font-mono overflow-y-auto h-full max-h-[300px] scrollbar-thin scrollbar-thumb-cyber-cyan/30">
                        {data?.rewritten_cv.latex_content || "% No preview available"}
                      </pre>
                      {/* Fade overlay */}
                      <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-black/80 to-transparent pointer-events-none"></div>
                  </div>
               </div>

               {/* Bottom Right: Logs */}
               <div className="lg:col-span-3 h-full min-h-[250px]">
                  <TerminalLog logs={data!.logs} />
               </div>

            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;