'use client';

import React from 'react';
import { Song } from '../types';
import { Activity, Music, BarChart3, Disc } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface HoloScreenProps {
    currentSong: Song | null;
}

const HoloScreen: React.FC<HoloScreenProps> = ({ currentSong }) => {
    return (
        <motion.div
            className="relative w-full h-full min-h-[400px] flex flex-col"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
        >
            {/* Main Hologram Glass */}
            <div className="relative flex-1 glass-panel rounded-sm overflow-hidden shadow-[0_0_30px_rgba(0,243,255,0.05)]">

                {/* Scanlines & Grid Overlay */}
                <div className="absolute inset-0 hologram-grid opacity-30 pointer-events-none z-0"></div>
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyber-cyan/5 to-transparent animate-scanline pointer-events-none z-10"></div>

                {/* HUD Corners - Animated */}
                <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-cyber-cyan opacity-70"></div>
                <div className="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-cyber-cyan opacity-70"></div>
                <div className="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-cyber-cyan opacity-70"></div>
                <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-cyber-cyan opacity-70"></div>

                {/* Content Area */}
                <div className="absolute inset-0 flex items-center justify-center z-20 p-6">
                    <AnimatePresence mode="wait">
                        {currentSong ? (
                            <motion.div
                                key={currentSong.id}
                                initial={{ opacity: 0, scale: 0.9, filter: "blur(10px)" }}
                                animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                                exit={{ opacity: 0, scale: 1.1, filter: "blur(10px)" }}
                                transition={{ duration: 0.5 }}
                                className="w-full h-full flex flex-col md:flex-row gap-8 items-center"
                            >
                                {/* Album Art Simulation (Spinning Disc) */}
                                <motion.div
                                    className="relative group shrink-0"
                                    initial={{ rotate: -90, opacity: 0 }}
                                    animate={{ rotate: 0, opacity: 1 }}
                                    transition={{ delay: 0.2, duration: 0.8 }}
                                >
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                                        className="w-48 h-48 rounded-full border-2 border-cyber-cyan/50 flex items-center justify-center"
                                    >
                                        <div className="w-40 h-40 rounded-full bg-slate-900 overflow-hidden relative">
                                            {currentSong.coverUrl ? (
                                                <img src={currentSong.coverUrl} alt="Cover" className="w-full h-full object-cover opacity-80" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center bg-gradient-to-tr from-slate-800 to-black">
                                                    <Disc className="w-16 h-16 text-slate-600" />
                                                </div>
                                            )}
                                        </div>
                                    </motion.div>
                                    {/* Glow behind disc */}
                                    <motion.div
                                        animate={{ opacity: [0.2, 0.5, 0.2], scale: [1, 1.1, 1] }}
                                        transition={{ duration: 4, repeat: Infinity }}
                                        className="absolute inset-0 rounded-full bg-cyber-cyan blur-2xl -z-10"
                                    ></motion.div>
                                </motion.div>

                                {/* Metadata HUD */}
                                <div className="flex-1 space-y-4 font-mono w-full">
                                    <div className="border-l-2 border-cyber-cyan pl-4 overflow-hidden">
                                        <motion.h3
                                            initial={{ x: -20, opacity: 0 }}
                                            animate={{ x: 0, opacity: 1 }}
                                            transition={{ delay: 0.3 }}
                                            className="text-xs text-cyber-cyan uppercase tracking-[0.3em] mb-1"
                                        >
                                            Sequence Id: {currentSong.id}
                                        </motion.h3>
                                        <motion.h1
                                            initial={{ x: -50, opacity: 0 }}
                                            animate={{ x: 0, opacity: 1 }}
                                            transition={{ delay: 0.4 }}
                                            className="text-3xl md:text-4xl font-bold text-white tracking-tighter uppercase drop-shadow-[0_0_5px_rgba(255,255,255,0.5)]"
                                        >
                                            {currentSong.title}
                                        </motion.h1>
                                        <motion.h2
                                            initial={{ x: -50, opacity: 0 }}
                                            animate={{ x: 0, opacity: 1 }}
                                            transition={{ delay: 0.5 }}
                                            className="text-xl text-slate-400"
                                        >
                                            {currentSong.artist}
                                        </motion.h2>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4 mt-6">
                                        <HudMetric
                                            delay={0.6}
                                            icon={<Activity size={14} />}
                                            label="BPM_RATE"
                                            value={currentSong.bpm || '---'}
                                            color="text-cyber-neon"
                                        />
                                        <HudMetric
                                            delay={0.7}
                                            icon={<Music size={14} />}
                                            label="KEY_SIG"
                                            value={currentSong.key || '---'}
                                            color="text-cyber-warn"
                                        />

                                        <motion.div
                                            initial={{ scaleX: 0, opacity: 0 }}
                                            animate={{ scaleX: 1, opacity: 1 }}
                                            transition={{ delay: 0.8, duration: 0.5 }}
                                            className="col-span-2 bg-cyber-slate/50 p-2 border border-slate-700/50 relative overflow-hidden origin-left"
                                        >
                                            <div className="flex items-center gap-2 text-cyber-cyan text-xs mb-1 relative z-10">
                                                <BarChart3 size={14} /> <span>ENERGY_VECTOR</span>
                                            </div>
                                            <div className="h-2 w-full bg-slate-800 rounded-full mt-2 overflow-hidden">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${currentSong.energy_level || 50}%` }}
                                                    transition={{ delay: 1, duration: 1, ease: "circOut" }}
                                                    className="h-full bg-cyber-cyan shadow-[0_0_10px_#00f3ff]"
                                                ></motion.div>
                                            </div>
                                        </motion.div>
                                    </div>
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="idle"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="text-center opacity-50"
                            >
                                <motion.div
                                    animate={{
                                        y: [0, -15, 0],
                                        opacity: [0.2, 0.4, 0.2],
                                        scale: [1, 1.05, 1]
                                    }}
                                    transition={{
                                        duration: 6,
                                        repeat: Infinity,
                                        ease: "easeInOut"
                                    }}
                                    className="text-cyber-cyan text-6xl mb-4"
                                >
                                    <Activity size={80} className="mx-auto" />
                                </motion.div>
                                <motion.p
                                    animate={{ opacity: [0.5, 1, 0.5] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                    className="text-cyber-cyan font-mono tracking-widest uppercase text-sm"
                                >
                                    System Idle. Awaiting Data Stream.
                                </motion.p>
                                <p className="text-slate-600 text-xs mt-2">Initiate Search or Activate Sensor Array</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Footer Technical Lines */}
                <div className="absolute bottom-0 w-full h-8 border-t border-cyber-cyan/20 bg-black/40 flex items-center px-4 justify-between text-[10px] text-cyber-cyan font-mono">
                    <span>SYS_STATUS: ONLINE</span>
                    <motion.span animate={{ opacity: [1, 0, 1] }} transition={{ duration: 0.5, repeat: Infinity, repeatDelay: 2 }}>_</motion.span>
                    <span>V_3.0.1</span>
                </div>
            </div>
        </motion.div>
    );
};

interface HudMetricProps {
    icon: React.ReactNode;
    label: string;
    value: string | number;
    color: string;
    delay: number;
}

const HudMetric: React.FC<HudMetricProps> = ({ icon, label, value, color, delay }) => (
    <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay }}
        className="bg-black/40 p-2 border border-cyber-cyan/20 box-glow"
    >
        <div className={`flex items-center gap-2 ${color} text-xs mb-1`}>
            {icon} <span>{label}</span>
        </div>
        <div className="text-xl font-tech">{value}</div>
    </motion.div>
);

export default HoloScreen;