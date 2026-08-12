import React, { useState, useEffect } from 'react';
import { BrainCircuit, Search, FileText, Scale, ShieldAlert, CheckCircle, Loader2 } from 'lucide-react';

const AI_STEPS = [
  { text: "Initializing AI Engine & verifying context...", icon: BrainCircuit, duration: 2000 },
  { text: "Analyzing case facts and officer input...", icon: Search, duration: 2500 },
  { text: "Structuring legal narrative & citations...", icon: FileText, duration: 4000 },
  { text: "Running constitutional compliance review...", icon: Scale, duration: 3000 },
  { text: "Checking for factual hallucinations...", icon: ShieldAlert, duration: 2500 },
  { text: "Finalizing court-ready document...", icon: CheckCircle, duration: 1000 }
];

const AIGenerationLoader = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let currentProgress = 0;
    const totalDuration = AI_STEPS.reduce((sum, step) => sum + step.duration, 0);
    const updateInterval = 100; // ms

    const progressTimer = setInterval(() => {
      currentProgress += (updateInterval / totalDuration) * 100;
      if (currentProgress > 95) currentProgress = 95; // Leave it at 95% until actually done
      setProgress(currentProgress);
    }, updateInterval);

    return () => clearInterval(progressTimer);
  }, []);

  useEffect(() => {
    let isCancelled = false;
    
    const runSteps = async () => {
      for (let i = 0; i < AI_STEPS.length; i++) {
        if (isCancelled) return;
        setCurrentStep(i);
        // Wait for the step duration
        await new Promise(resolve => setTimeout(resolve, AI_STEPS[i].duration));
      }
      // If it takes longer, loop the last few steps or just stay at the end
      if (!isCancelled) {
        setCurrentStep(AI_STEPS.length - 1);
      }
    };

    runSteps();
    
    return () => {
      isCancelled = true;
    };
  }, []);

  const ActiveIcon = AI_STEPS[currentStep].icon;

  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-8 bg-slate-50/50">
      <div className="relative mb-8 mt-12">
        {/* Pulsing background glow */}
        <div className="absolute inset-0 bg-indigo-500/20 blur-2xl rounded-full animate-pulse scale-150"></div>
        
        {/* Icon container */}
        <div className="relative z-10 w-24 h-24 bg-white rounded-2xl shadow-xl border border-indigo-100 flex items-center justify-center transition-all duration-500 transform hover:scale-105">
          <ActiveIcon className="w-10 h-10 text-indigo-600 animate-pulse" />
          
          {/* Small corner spinner to indicate active processing */}
          <div className="absolute -bottom-2 -right-2 bg-indigo-600 rounded-full p-1.5 shadow-lg">
            <Loader2 className="w-4 h-4 text-white animate-spin" />
          </div>
        </div>
      </div>

      <div className="max-w-md w-full mx-auto mt-4 space-y-6">
        <div>
          <h3 className="text-xl font-bold text-slate-800 transition-opacity duration-300">
            {AI_STEPS[currentStep].text}
          </h3>
          <p className="text-slate-400 text-sm mt-2">
            This can take a few minutes. This page updates automatically — no need to refresh.
          </p>
        </div>

        {/* Progress Bar Container */}
        <div className="bg-slate-200 h-2.5 w-full rounded-full overflow-hidden shadow-inner">
          <div 
            className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-blue-500 rounded-full transition-all duration-300 ease-out relative"
            style={{ width: `${progress}%` }}
          >
            {/* Shimmer effect */}
            <div className="absolute top-0 right-0 bottom-0 left-0 bg-white/20 animate-[shimmer_2s_infinite] -skew-x-12"></div>
          </div>
        </div>
        
        {/* Steps Tracker */}
        <div className="flex justify-between items-center px-2">
          {AI_STEPS.map((step, index) => (
            <div 
              key={index} 
              className={`w-2 h-2 rounded-full transition-all duration-500 ${
                index === currentStep 
                  ? 'bg-indigo-600 scale-150 ring-2 ring-indigo-200' 
                  : index < currentStep 
                    ? 'bg-indigo-300' 
                    : 'bg-slate-200'
              }`}
              title={step.text}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default AIGenerationLoader;
