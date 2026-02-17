import React from 'react';
import { motion } from 'framer-motion';

interface ScoreGaugeProps {
  score: number;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({ score }) => {
  const radius = 80;
  const stroke = 12;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // Determine color based on score
  let color = '#ef4444'; // Red
  if (score >= 80) color = '#00ff9d'; // Cyber Green
  else if (score >= 60) color = '#fbbf24'; // Yellow

  return (
    <div className="relative flex items-center justify-center w-64 h-64">
      {/* Background Circle */}
      <svg
        height={radius * 2}
        width={radius * 2}
        className="rotate-[-90deg]"
      >
        <circle
          stroke="#1f2937"
          strokeWidth={stroke}
          fill="transparent"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        {/* Progress Circle */}
        <motion.circle
          stroke={color}
          fill="transparent"
          strokeWidth={stroke}
          strokeDasharray={circumference + ' ' + circumference}
          style={{ strokeDashoffset }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 2, ease: "easeOut" }}
        />
      </svg>
      
      {/* Inner Content */}
      <div className="absolute flex flex-col items-center justify-center">
        <motion.span 
            className="text-5xl font-display font-bold text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
        >
          {score.toFixed(1)}
        </motion.span>
        <span className="text-sm font-mono text-gray-400 mt-2 tracking-widest">FIT_SCORE</span>
      </div>

      {/* Decorative Rings */}
      <div className="absolute inset-0 border border-cyber-gray rounded-full animate-pulse-fast opacity-30"></div>
      <div className="absolute -inset-4 border border-dashed border-cyber-greenDim rounded-full animate-[spin_10s_linear_infinite]"></div>
    </div>
  );
};
