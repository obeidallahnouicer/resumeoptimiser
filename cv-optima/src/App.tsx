/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { MainLayout } from './components/layout/MainLayout';
import { StageProgress, Stage } from './components/ui/StageProgress';
import { UploadStage } from './components/stages/UploadStage';
import { ParseStage } from './components/stages/ParseStage';
import { MatchStage } from './components/stages/MatchStage';
import { ExplainStage } from './components/stages/ExplainStage';
import { RewriteStage } from './components/stages/RewriteStage';
import { CompareStage } from './components/stages/CompareStage';
import { PipelineProvider } from './context/PipelineContext';

export default function App() {
  const [currentStage, setCurrentStage] = useState<Stage>('upload');

  const handleStageComplete = (nextStage: Stage) => {
    setCurrentStage(nextStage);
  };

  const renderStage = () => {
    switch (currentStage) {
      case 'upload':
        return <UploadStage onComplete={() => handleStageComplete('parse')} />;
      case 'parse':
        return <ParseStage onComplete={() => handleStageComplete('match')} />;
      case 'match':
        return <MatchStage onComplete={() => handleStageComplete('explain')} />;
      case 'explain':
        return <ExplainStage onComplete={() => handleStageComplete('rewrite')} />;
      case 'rewrite':
        return <RewriteStage onComplete={() => handleStageComplete('compare')} />;
      case 'compare':
        return <CompareStage onReset={() => handleStageComplete('upload')} />;
      default:
        return <UploadStage onComplete={() => handleStageComplete('parse')} />;
    }
  };

  return (
    <PipelineProvider>
    <MainLayout>
      <StageProgress currentStage={currentStage} />
      
      <div className="flex-1 flex items-center justify-center w-full relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStage}
            className="w-full h-full flex flex-col items-center justify-center"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
          >
            {renderStage()}
          </motion.div>
        </AnimatePresence>
      </div>
    </MainLayout>
    </PipelineProvider>
  );
}
