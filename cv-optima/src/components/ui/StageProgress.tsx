import { motion } from 'motion/react';
import { Check } from 'lucide-react';

export type Stage = 'upload' | 'parse' | 'match' | 'explain' | 'rewrite' | 'compare';

interface StageProgressProps {
  currentStage: Stage;
}

const STAGES: { id: Stage; label: string }[] = [
  { id: 'upload', label: 'Upload' },
  { id: 'parse', label: 'Parse' },
  { id: 'match', label: 'Match' },
  { id: 'explain', label: 'Explain' },
  { id: 'rewrite', label: 'Rewrite' },
  { id: 'compare', label: 'Compare' },
];

export function StageProgress({ currentStage }: StageProgressProps) {
  const currentIndex = STAGES.findIndex((s) => s.id === currentStage);

  return (
    <div className="w-full flex justify-center mb-12 relative">
      {/* Connecting Line */}
      <div className="absolute top-1/2 left-0 w-full h-[1px] bg-border -z-10" />
      
      {/* Active Progress Line */}
      <motion.div 
        className="absolute top-1/2 left-0 h-[1px] bg-accent shadow-[0_0_8px_var(--color-accent)] -z-10"
        initial={{ width: '0%' }}
        animate={{ width: `${(currentIndex / (STAGES.length - 1)) * 100}%` }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
      />

      <div className="flex justify-between w-full max-w-3xl relative">
        {STAGES.map((stage, index) => {
          const isActive = index === currentIndex;
          const isCompleted = index < currentIndex;

          return (
            <div key={stage.id} className="flex flex-col items-center gap-3 relative group">
              <motion.div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center border transition-colors duration-300
                  ${isActive 
                    ? 'bg-bg-primary border-accent shadow-[0_0_15px_var(--color-accent-dim)]' 
                    : isCompleted 
                      ? 'bg-accent border-accent text-bg-primary' 
                      : 'bg-bg-primary border-border text-text-secondary'}
                `}
                initial={false}
                animate={{
                  scale: isActive ? 1.1 : 1,
                }}
              >
                {isCompleted ? (
                  <Check className="w-4 h-4" strokeWidth={3} />
                ) : (
                  <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-accent animate-pulse' : 'bg-border'}`} />
                )}
              </motion.div>
              
              <span 
                className={`
                  text-xs font-medium tracking-wide uppercase absolute -bottom-6 whitespace-nowrap transition-colors duration-300
                  ${isActive ? 'text-accent' : isCompleted ? 'text-text-primary' : 'text-text-secondary'}
                `}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
