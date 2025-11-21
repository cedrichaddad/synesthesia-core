'use client';

import React from 'react';
import { motion } from 'framer-motion';
import HoloScreen from './HoloScreen';
import SynthRack from './SynthRack';
import TerminalInput from './TerminalInput';
import AudioSensor from './AudioSensor';
import { useSynesthesia } from '../hooks/useSynesthesia';
import { Song } from '../types';
import { ArrowRight } from 'lucide-react';

const LabWorkbench: React.FC = () => {
    const {
        currentSong,
        setCurrentSong,
        recommendations,
        searchResults,
        isSearching,
        sensorState,
        knobs,
        updateKnob,
        addKnob,
        handleSearch,
        startListening,
        fetchRecommendations
    } = useSynesthesia();

    return (
        <div className="min-h-screen w-full bg-cyber-black text-gray-300 font-sans overflow-hidden relative flex flex-col">

            {/* Animated Background Environment */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
                <motion.div
                    initial={{ scale: 1.1 }}
                    animate={{
                        scale: [1.1, 1.15, 1.1],
                        x: [0, -10, 0],
                    }}
                    transition={{
                        duration: 20,
                        repeat: Infinity,
                        ease: "linear"
                    }}
                    className="absolute inset-0 bg-cover bg-center opacity-30 pixel-texture"
                    // A messier, darker, more detailed sci-fi background
                    style={{ backgroundImage: "url('https://images.unsplash.com/photo-1572435555641-701a24c32cc5?q=80&w=2070&auto=format&fit=crop')" }}
                />
                {/* Overlay Gradients for depth */}
                <div className="absolute inset-0 bg-gradient-to-t from-cyber-black via-cyber-black/70 to-transparent"></div>
                <div className="absolute inset-0 bg-gradient-to-r from-cyber-black/80 via-transparent to-cyber-black/80"></div>

                {/* CRT Scanline Effect */}
                <div className="absolute inset-0 crt-overlay opacity-20"></div>
            </div>

            {/* Top Bar */}
            <motion.header
                initial={{ y: -50, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="relative z-50 px-6 py-4 flex justify-between items-center border-b border-slate-800/50 backdrop-blur-sm"
            >
                <div className="flex items-center gap-3">
                    <motion.div
                        animate={{ opacity: [1, 0.5, 1] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="w-3 h-3 bg-cyber-neon rounded-full shadow-[0_0_10px_#00ff41]"
                    ></motion.div>
                    <h1 className="text-lg font-tech font-bold tracking-widest text-white uppercase">Synesthesia <span className="text-slate-500">/ LAB_V.0.9</span></h1>
                </div>
                <div className="hidden md:block text-xs font-mono text-slate-500">
                    <TypewriterText text="CPU_LOAD: 12% // MEMORY_ALLOC: 32GB // UPTIME: 412h" />
                </div>
            </motion.header>

            {/* Main Workspace */}
            <main className="relative z-10 flex-1 p-4 md:p-8 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1800px] mx-auto w-full overflow-y-auto lg:overflow-visible">

                {/* Left Column: Input & Tools (4 Cols) */}
                <div className="lg:col-span-4 flex flex-col gap-6">
                    {/* Search Module */}
                    <motion.section
                        initial={{ x: -50, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.2, duration: 0.6 }}
                        className="flex flex-col gap-2"
                    >
                        <label className="text-xs font-mono text-cyber-cyan uppercase tracking-wider mb-1">
                            <span className="mr-2 text-slate-600">01.</span> Input Terminal
                        </label>
                        <TerminalInput
                            onSearch={handleSearch}
                            results={searchResults}
                            onSelect={(song: Song) => {
                                setCurrentSong(song);
                                // Simulate automated recommendation fetch on select
                                setTimeout(fetchRecommendations, 500);
                            }}
                            isSearching={isSearching}
                        />
                    </motion.section>

                    {/* Audio Sensor Module */}
                    <motion.section
                        initial={{ x: -50, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.4, duration: 0.6 }}
                        className="flex flex-col gap-2 items-center p-6 border border-slate-800 bg-black/40 rounded-lg backdrop-blur-sm shadow-[0_0_15px_rgba(0,0,0,0.5)]"
                    >
                        <label className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-4 w-full text-left">
                            <span className="mr-2 text-slate-600">02.</span> Audio Identification
                        </label>
                        <AudioSensor state={sensorState} onActivate={startListening} />
                    </motion.section>

                    {/* Control Board */}
                    <motion.section
                        initial={{ x: -50, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.6, duration: 0.6 }}
                        className="flex-1 min-h-[300px]"
                    >
                        <label className="text-xs font-mono text-cyber-neon uppercase tracking-wider mb-2 block">
                            <span className="mr-2 text-slate-600">03.</span> Vector Arithmetic
                        </label>
                        <SynthRack knobs={knobs} onUpdate={updateKnob} onAdd={addKnob} />

                        <motion.button
                            whileHover={{ scale: 1.02, backgroundColor: 'rgba(0, 243, 255, 0.1)' }}
                            whileTap={{ scale: 0.98 }}
                            onClick={fetchRecommendations}
                            className="mt-4 w-full py-3 bg-cyber-slate border border-cyber-cyan/30 text-cyber-cyan font-mono text-sm uppercase tracking-widest transition-colors flex items-center justify-center gap-2 group"
                        >
                            Calculate Recommendations <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
                        </motion.button>
                    </motion.section>
                </div>

                {/* Right Column: Visualization (8 Cols) */}
                <div className="lg:col-span-8 min-h-[500px] flex flex-col gap-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.4, duration: 0.8 }}
                    >
                        <label className="text-xs font-mono text-cyber-cyan uppercase tracking-wider mb-2 block">
                            <span className="mr-2 text-slate-600">04.</span> Main Holographic Projector
                        </label>
                        <HoloScreen currentSong={currentSong} />
                    </motion.div>

                    {/* Recommendations Readout */}
                    {recommendations.length > 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="h-48 border-t border-slate-800 mt-4 pt-4 overflow-hidden"
                        >
                            <h3 className="text-xs font-mono text-slate-400 mb-3">COMPUTED_RESULTS_QUEUE:</h3>
                            <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
                                {recommendations.map((rec, idx) => (
                                    <motion.div
                                        key={rec.id}
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.1 }}
                                        className="min-w-[200px] bg-slate-900/80 border border-slate-700 p-3 hover:border-cyber-cyan cursor-pointer transition-colors relative group"
                                        onClick={() => setCurrentSong(rec)}
                                    >
                                        <div className="absolute inset-0 bg-cyber-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                                        <div className="w-full h-1 bg-gradient-to-r from-cyber-neon to-transparent mb-2"></div>
                                        <h4 className="text-sm font-bold text-white truncate relative z-10">{rec.title}</h4>
                                        <p className="text-xs text-slate-400 truncate relative z-10">{rec.artist}</p>
                                        <div className="flex justify-between mt-2 text-[10px] font-mono text-slate-500 relative z-10">
                                            <span>{rec.bpm} BPM</span>
                                            <span>{rec.energy_level}% NRG</span>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </div>

            </main>

        </div>
    );
};

// Simple Typewriter effect component for header
const TypewriterText = ({ text }: { text: string }) => {
    return (
        <span className="animate-pulse">{text}</span>
    )
}

export default LabWorkbench;