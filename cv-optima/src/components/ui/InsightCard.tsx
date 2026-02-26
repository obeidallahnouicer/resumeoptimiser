import { motion } from 'motion/react';
import { AlertTriangle, Lightbulb, ArrowRight } from 'lucide-react';

interface InsightCardProps {
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  index: number;
}

export function InsightCard({ title, description, severity, index }: InsightCardProps) {
  const severityColor = {
    high: 'bg-error',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500',
  };

  return (
    <motion.div 
      className="relative bg-bg-card border border-border rounded-xl p-6 overflow-hidden group hover:border-text-secondary transition-colors cursor-pointer"
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ y: -2 }}
    >
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${severityColor[severity]}`} />
      
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {severity === 'high' ? (
            <AlertTriangle className="w-5 h-5 text-error" />
          ) : (
            <Lightbulb className="w-5 h-5 text-accent" />
          )}
          <h4 className="font-semibold text-text-primary">{title}</h4>
        </div>
        <span className={`text-xs font-mono uppercase px-2 py-1 rounded bg-bg-primary border border-border ${severity === 'high' ? 'text-error' : 'text-text-secondary'}`}>
          {severity} Priority
        </span>
      </div>
      
      <p className="text-sm text-text-secondary leading-relaxed pl-7">
        {description}
      </p>

      <div className="absolute right-4 bottom-4 opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-2 group-hover:translate-x-0">
        <ArrowRight className="w-5 h-5 text-text-primary" />
      </div>
    </motion.div>
  );
}
