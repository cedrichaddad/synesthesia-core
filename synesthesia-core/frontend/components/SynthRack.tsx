'use client';

import React, { useState, useRef, useEffect } from 'react';
import Knob from './ui/Knob';
import { KnobState, KnobConfig } from '../types';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Check, X, Settings2 } from 'lucide-react';

interface SynthRackProps {
    knobs: KnobState;
    config: KnobConfig | null;
    onUpdate: (name: string, val: number) => void;
    onAdd: (name: string) => void;
}

const SynthRack: React.FC<SynthRackProps> = ({ knobs, config, onUpdate, onAdd }) => {
    const [isAdding, setIsAdding] = useState(false);
    const [newKnobName, setNewKnobName] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isAdding && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isAdding]);

    const handleAddSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (newKnobName.trim()) {
            onAdd(newKnobName);
            setNewKnobName('');
            setIsAdding(false);
        }
    };

    const handleCancel = () => {
        setIsAdding(false);
        setNewKnobName('');
    };

    return (
        <div className="glass-panel rounded-md p-8 shadow-[inset_0_0_50px_rgba(0,0,0,0.8)] relative overflow-hidden min-h-[300px] flex flex-col items-center justify-center">
            {/* Hex Bolts */}
            <div className="absolute top-3 left-3 w-4 h-4 text-cyber-slate/50"><Settings2 size={20} /></div>
            <div className="absolute top-3 right-3 w-4 h-4 text-cyber-slate/50"><Settings2 size={20} /></div>
            <div className="absolute bottom-3 left-3 w-4 h-4 text-cyber-slate/50"><Settings2 size={20} /></div>
            <div className="absolute bottom-3 right-3 w-4 h-4 text-cyber-slate/50"><Settings2 size={20} /></div>

            {/* Label */}
            <div className="absolute top-3 left-1/2 -translate-x-1/2 text-cyber-cyan font-tech font-bold tracking-[0.3em] text-sm border border-cyber-cyan/30 px-4 py-1 rounded bg-black/60 flex items-center gap-2 text-glow shadow-[0_0_10px_rgba(0,243,255,0.1)]">
                <Settings2 size={12} className="text-cyber-neon" /> FREQ_MODULATOR_V2
            </div>

            <motion.div
                className="flex flex-row justify-center gap-12 mt-12 items-center flex-wrap w-full max-w-4xl"
                initial="hidden"
                animate="visible"
                variants={{
                    visible: { transition: { staggerChildren: 0.05 } }
                }}
            >
                {config ? (
                    // Render from Config
                    config.knobs.map((knobDef) => (
                        <motion.div
                            key={knobDef.id}
                            className="flex justify-center"
                            variants={{
                                hidden: { opacity: 0, y: 20 },
                                visible: { opacity: 1, y: 0 }
                            }}
                            layout
                        >
                            <Knob
                                label={knobDef.label}
                                value={knobs[knobDef.id] ?? 50} // Default to 50 if not found
                                onChange={(val: number) => onUpdate(knobDef.id, val)}
                                color={knobDef.color}
                            />
                        </motion.div>
                    ))
                ) : (
                    // Fallback / Loading State
                    <div className="col-span-3 text-center text-xs font-mono text-slate-500 animate-pulse">
                        LOADING_CONFIG...
                    </div>
                )}

                {/* Add Module Slot */}
                <motion.div
                    className="flex justify-center items-center min-h-[100px]"
                    variants={{
                        hidden: { opacity: 0 },
                        visible: { opacity: 1 }
                    }}
                    layout
                >
                    <AnimatePresence mode="wait">
                        {isAdding ? (
                            <motion.form
                                initial={{ scale: 0.8, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.8, opacity: 0 }}
                                onSubmit={handleAddSubmit}
                                className="w-20 h-20 flex flex-col items-center justify-center gap-1"
                            >
                                <input
                                    ref={inputRef}
                                    type="text"
                                    value={newKnobName}
                                    onChange={(e) => setNewKnobName(e.target.value)}
                                    placeholder="TAG"
                                    className="w-full bg-black/50 border border-cyber-neon/50 text-cyber-neon text-[10px] text-center font-mono p-1 outline-none focus:border-cyber-neon uppercase placeholder-cyber-neon/30 rounded-sm"
                                    maxLength={10}
                                />
                                <div className="flex gap-1 w-full">
                                    <button
                                        type="submit"
                                        className="flex-1 bg-cyber-neon/20 hover:bg-cyber-neon/40 text-cyber-neon flex items-center justify-center py-1 rounded-sm transition-colors"
                                    >
                                        <Check size={12} />
                                    </button>
                                    <button
                                        type="button"
                                        onClick={handleCancel}
                                        className="flex-1 bg-cyber-danger/20 hover:bg-cyber-danger/40 text-cyber-danger flex items-center justify-center py-1 rounded-sm transition-colors"
                                    >
                                        <X size={12} />
                                    </button>
                                </div>
                            </motion.form>
                        ) : (
                            <motion.button
                                initial={{ opacity: 0.5 }}
                                whileHover={{ opacity: 1, scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => setIsAdding(true)}
                                className="w-16 h-16 rounded-full border-2 border-dashed border-zinc-700 text-zinc-600 hover:text-cyber-neon hover:border-cyber-neon/50 flex flex-col items-center justify-center gap-1 transition-all duration-300 group"
                            >
                                <Plus size={20} className="group-hover:rotate-90 transition-transform duration-300" />
                                <span className="text-[8px] font-mono tracking-widest uppercase group-hover:text-cyber-neon">ADD_MOD</span>
                            </motion.button>
                        )}
                    </AnimatePresence>
                </motion.div>

            </motion.div>
        </div>
    );
};

export default SynthRack;