'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface MissionLogProps {
    stats: {
        processingTime: string;
        fingerprintCount: number;
        vector?: number[];
    } | null;
}

const MissionLog: React.FC<MissionLogProps> = ({ stats }) => {
    const [logs, setLogs] = useState<string[]>([]);

    useEffect(() => {
        if (stats) {
            const newLogs = [
                `[SYSTEM] Analysis Complete`,
                `[RUST] Core Active`,
                `[FFT] Window: 4096 / Hop: 2048`,
                `[METRICS] Time: ${stats.processingTime}`,
                `[METRICS] Fingerprints: ${stats.fingerprintCount}`,
                `[VECTOR] Dim: 512 / Norm: L2`,
                `[STATUS] Target Locked`
            ];
            setLogs(newLogs);
        } else {
            setLogs(['[SYSTEM] Awaiting Input...', '[SENSORS] Idle']);
        }
    }, [stats]);

    return (
        <div className="w-full h-full bg-black/80 border border-cyber-slate/50 rounded-sm p-4 font-mono text-xs overflow-hidden relative shadow-[inset_0_0_20px_rgba(0,0,0,0.8)]">
            {/* Scanline effect */}
            <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.5)_50%)] bg-[length:100%_4px] pointer-events-none opacity-20"></div>

            {/* Header */}
            <div className="flex justify-between items-center border-b border-cyber-slate/30 pb-2 mb-2">
                <span className="text-cyber-blue font-bold tracking-widest">MISSION LOG // T-800</span>
                <div className="flex gap-1">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-yellow-500 rounded-full opacity-50"></div>
                    <div className="w-2 h-2 bg-green-500 rounded-full opacity-50"></div>
                </div>
            </div>

            {/* Content */}
            <div className="flex flex-col gap-1 text-emerald-500/90 h-[120px] overflow-y-auto scrollbar-hide">
                <AnimatePresence mode='wait'>
                    {logs.map((log, i) => (
                        <motion.div
                            key={i + log} // Unique key to trigger animation
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.1, duration: 0.2 }}
                        >
                            <span className="opacity-50 mr-2">{`>`}</span>
                            {log}
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            {/* Footer Decor */}
            <div className="absolute bottom-2 right-2 text-[10px] text-cyber-slate opacity-50">
                V.0.9.2-ALPHA
            </div>
        </div>
    );
};

export default MissionLog;
