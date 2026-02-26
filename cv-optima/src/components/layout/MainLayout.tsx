import { motion } from 'motion/react';
import { ReactNode } from 'react';

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-bg-primary text-text-primary flex flex-col items-center relative overflow-hidden">
      {/* Subtle ambient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-accent/5 rounded-full blur-[120px] pointer-events-none" />
      
      <header className="w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center border border-accent/20">
            <div className="w-3 h-3 bg-accent rounded-full shadow-[0_0_10px_var(--color-accent)]" />
          </div>
          <span className="font-semibold tracking-tight text-lg">CV Optima</span>
        </div>
        <div className="text-xs font-mono text-text-secondary tracking-widest uppercase opacity-60">
          AI Optimization Engine v2.0
        </div>
      </header>

      <main className="w-full max-w-5xl mx-auto px-6 py-8 flex-1 flex flex-col z-10">
        {children}
      </main>
    </div>
  );
}
