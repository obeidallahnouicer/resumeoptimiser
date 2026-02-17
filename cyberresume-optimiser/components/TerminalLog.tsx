import React, { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';

interface TerminalLogProps {
  logs: string[];
}

export const TerminalLog: React.FC<TerminalLogProps> = ({ logs }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="w-full h-full bg-cyber-black border border-cyber-gray rounded-lg overflow-hidden flex flex-col font-mono text-xs md:text-sm shadow-[0_0_20px_rgba(0,0,0,0.5)]">
      <div className="flex items-center justify-between px-4 py-2 bg-cyber-dark border-b border-cyber-gray">
        <div className="flex items-center gap-2 text-cyber-green">
          <Terminal size={14} />
          <span className="uppercase tracking-widest opacity-80">System_Log</span>
        </div>
        <div className="flex gap-1">
            <div className="w-2 h-2 rounded-full bg-red-500/20"></div>
            <div className="w-2 h-2 rounded-full bg-yellow-500/20"></div>
            <div className="w-2 h-2 rounded-full bg-green-500/50"></div>
        </div>
      </div>
      <div className="flex-1 p-4 overflow-y-auto space-y-1 scrollbar-thin scrollbar-thumb-cyber-green scrollbar-track-cyber-dark">
        {logs.length === 0 ? (
           <span className="text-gray-600 animate-pulse">Waiting for input stream...</span>
        ) : (
            logs.map((log, index) => (
            <div key={index} className="flex gap-2">
                <span className="text-cyber-green opacity-50 shrink-0">{`>`}</span>
                <span className={`${
                    log.includes('[SUCCESS]') ? 'text-cyber-green' : 
                    log.includes('[ERROR]') ? 'text-cyber-pink' : 
                    log.includes('[WARN]') ? 'text-yellow-400' : 'text-gray-300'
                }`}>
                {log}
                </span>
            </div>
            ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
