import { motion } from 'motion/react';

interface HeroScoreProps {
  score: number;
  label: string;
}

export function HeroScore({ score, label }: HeroScoreProps) {
  return (
    <div className="flex flex-col items-center justify-center relative">
      <div className="relative w-48 h-48 flex items-center justify-center">
        {/* Background Ring */}
        <svg className="absolute w-full h-full transform -rotate-90">
          <circle
            cx="96"
            cy="96"
            r="88"
            stroke="var(--color-bg-card)"
            strokeWidth="12"
            fill="transparent"
          />
          {/* Progress Ring */}
          <motion.circle
            cx="96"
            cy="96"
            r="88"
            stroke="var(--color-accent)"
            strokeWidth="12"
            fill="transparent"
            strokeDasharray={552} // 2 * PI * 88
            strokeDashoffset={552}
            strokeLinecap="round"
            initial={{ strokeDashoffset: 552 }}
            animate={{ strokeDashoffset: 552 - (552 * score) / 100 }}
            transition={{ duration: 1.5, ease: "easeOut" }}
          />
        </svg>
        
        <div className="flex flex-col items-center">
          <motion.span 
            className="text-6xl font-bold text-text-primary tracking-tighter"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            {score}%
          </motion.span>
        </div>
      </div>
      <span className="mt-4 text-sm font-medium text-text-secondary uppercase tracking-widest">{label}</span>
    </div>
  );
}
