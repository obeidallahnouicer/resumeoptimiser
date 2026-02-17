import React from 'react';
import { motion } from 'framer-motion';

interface GlitchTextProps {
  text: string;
  className?: string;
  as?: 'h1' | 'h2' | 'h3' | 'p' | 'span';
}

export const GlitchText: React.FC<GlitchTextProps> = ({ text, className = '', as = 'span' }) => {
  const Component = motion[as];

  return (
    <div className="relative inline-block group">
      <Component className={`relative z-10 ${className}`}>
        {text}
      </Component>
      <Component 
        className={`absolute top-0 left-0 -z-10 w-full h-full text-cyber-green opacity-0 group-hover:opacity-70 group-hover:animate-glitch ${className}`}
        style={{ clipPath: 'polygon(0 0, 100% 0, 100% 35%, 0 35%)', transform: 'translate(-2px)' }}
        aria-hidden="true"
      >
        {text}
      </Component>
      <Component 
        className={`absolute top-0 left-0 -z-10 w-full h-full text-cyber-pink opacity-0 group-hover:opacity-70 group-hover:animate-glitch ${className}`}
        style={{ clipPath: 'polygon(0 65%, 100% 65%, 100% 100%, 0 100%)', transform: 'translate(2px)', animationDelay: '0.1s' }}
        aria-hidden="true"
      >
        {text}
      </Component>
    </div>
  );
};
