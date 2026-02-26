import { motion } from 'motion/react';
import { UploadCloud, FileText, Loader2, AlertCircle } from 'lucide-react';
import { useState, useCallback, DragEvent, useRef } from 'react';
import { usePipeline } from '../../context/PipelineContext';
import { extractCVText, ApiError } from '../../api';

interface UploadStageProps {
  onComplete: () => void;
}

export function UploadStage({ onComplete }: UploadStageProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [jobText, setJobText] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { setRawInputs, setError } = usePipeline();

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault(); setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault(); setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault(); setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }, []);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = e.target.files?.[0];
    if (picked) setFile(picked);
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!file) { setErrorMsg('Please upload your CV file.'); return; }
    if (!jobText.trim()) { setErrorMsg('Please paste the job description.'); return; }
    setErrorMsg('');
    setIsProcessing(true);
    try {
      const result = await extractCVText(file, jobText);
      setRawInputs(result.cv_text, jobText, result.filename);
      onComplete();
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Failed to process file.';
      setErrorMsg(msg);
      setError(msg);
    } finally {
      setIsProcessing(false);
    }
  }, [file, jobText, setRawInputs, setError, onComplete]);

  return (
    <motion.div
      className="w-full flex flex-col items-center gap-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div
        className={`relative w-full max-w-2xl h-52 rounded-3xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center cursor-pointer
          ${isDragging ? 'border-accent bg-accent/5 shadow-[0_0_30px_var(--color-accent-dim)]' : file ? 'border-success bg-success/5' : 'border-border bg-bg-card hover:border-text-secondary'}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input ref={fileInputRef} type="file" accept=".pdf,.docx" className="hidden" onChange={handleFileChange} />
        {file ? (
          <div className="flex flex-col items-center gap-3">
            <FileText className="w-10 h-10 text-success" />
            <span className="text-text-primary font-medium">{file.name}</span>
            <span className="text-xs text-text-secondary">{(file.size / 1024).toFixed(0)} KB</span>
          </div>
        ) : (
          <>
            <UploadCloud className={`w-10 h-10 mb-3 ${isDragging ? 'text-accent' : 'text-text-secondary'}`} />
            <span className="text-text-primary font-medium">Drop your CV here</span>
            <span className="text-xs text-text-secondary mt-1">PDF or DOCX · max 10 MB</span>
          </>
        )}
      </div>

      <div className="w-full max-w-2xl flex flex-col gap-2">
        <label className="text-sm font-medium text-text-secondary uppercase tracking-wider">Job Description</label>
        <textarea
          className="w-full h-40 bg-bg-card border border-border rounded-xl p-4 text-sm text-text-primary placeholder-text-secondary resize-none focus:outline-none focus:border-accent transition-colors"
          placeholder="Paste the full job description here…"
          value={jobText}
          onChange={(e) => setJobText(e.target.value)}
        />
      </div>

      {errorMsg && (
        <div className="flex items-center gap-2 text-error text-sm">
          <AlertCircle className="w-4 h-4" />{errorMsg}
        </div>
      )}

      <motion.button
        className="flex items-center gap-2 px-8 py-3 bg-accent text-bg-primary font-semibold rounded-xl hover:bg-white transition-colors disabled:opacity-40"
        onClick={handleSubmit}
        disabled={isProcessing}
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
      >
        {isProcessing ? <><Loader2 className="w-4 h-4 animate-spin" /> Processing…</> : 'Analyze CV'}
      </motion.button>
    </motion.div>
  );
}
