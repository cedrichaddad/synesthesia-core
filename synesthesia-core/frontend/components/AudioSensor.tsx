'use client';

import React from 'react';
import { Mic, Radio, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { SensorState } from '../types';

interface AudioSensorProps {
    state: SensorState;
    onActivate: () => void;
}

const AudioSensor: React.FC<AudioSensorProps> = ({ state, onActivate }) => {

    // Dynamic styles based on state
    const getStatusColor = () => {
        switch (state) {
            case SensorState.LISTENING: return 'text-cyber-danger border-cyber-danger shadow-cyber-danger/50';
            case SensorState.PROCESSING: return 'text-cyber-warn border-cyber-warn shadow-cyber-warn/50';
            case SensorState.SUCCESS: return 'text-cyber-neon border-cyber-neon shadow-cyber-neon/50';
            case SensorState.ERROR: return 'text-red-600 border-red-600';
            default: return 'text-slate-500 border-slate-700 hover:text-cyber-neon hover:border-cyber-neon';
        }
    };

    const getGlow = () => {
        if (state === SensorState.LISTENING) return 'shadow-[0_0_30px_rgba(255,0,60,0.6)] animate-pulse';
        if (state === SensorState.PROCESSING) return 'shadow-[0_0_20px_rgba(255,183,0,0.6)]';
        return '';
    };

    return (
        <div className="flex flex-col items-center">
            {/* Label */}
            <div className="mb-2 text-[10px] font-mono text-slate-500 tracking-widest uppercase">
                Sensor_Array_01
            </div>

            {/* Physical Button Container */}
            <button
                onClick={state === SensorState.IDLE ? onActivate : undefined}
                disabled={state !== SensorState.IDLE}
                className={`relative w-24 h-24 rounded-xl bg-zinc-900 border-2 transition-all duration-300 group ${getStatusColor()} ${getGlow()} flex items-center justify-center overflow-hidden`}
            >
                {/* Background Grid Texture */}
                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle,currentColor_1px,transparent_1px)] bg-[size:4px_4px]"></div>

                {/* Icon Content */}
                <div className="relative z-10">
                    {state === SensorState.IDLE && <Mic size={32} className="transition-transform group-hover:scale-110" />}
                    {state === SensorState.LISTENING && <Radio size={32} className="animate-ping absolute opacity-75" />}
                    {state === SensorState.LISTENING && <Mic size={32} />}
                    {state === SensorState.PROCESSING && <Loader2 size={32} className="animate-spin" />}
                    {state === SensorState.SUCCESS && <CheckCircle2 size={32} />}
                    {state === SensorState.ERROR && <AlertCircle size={32} />}
                </div>

                {/* Status Text Overlay */}
                <div className="absolute bottom-1 left-0 right-0 text-[8px] font-bold text-center uppercase tracking-wider">
                    {state === SensorState.IDLE && "ARMED"}
                    {state === SensorState.LISTENING && "REC"}
                    {state === SensorState.PROCESSING && "PROC"}
                    {state === SensorState.SUCCESS && "OK"}
                    {state === SensorState.ERROR && "ERR"}
                </div>
            </button>
        </div>
    );
};

export default AudioSensor;