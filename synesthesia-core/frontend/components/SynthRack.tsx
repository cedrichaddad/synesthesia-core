'use client';

import React, { useState, useRef, useEffect } from 'react';
import Knob from './ui/Knob';
import { KnobState } from '../types';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Check, X, Settings2 } from 'lucide-react';

interface SynthRackProps {
    knobs: KnobState;
    onUpdate: (name: string, val: number) => void;
    onAdd: (name: string) => void;
}

const SynthRack: React.FC<SynthRackProps> = ({ knobs, onUpdate, onAdd }) => {
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
        <div className="bg-zinc-900 border-t-4 border-slate-800 rounded-md p-6 shadow-[inset_0_0_20px_rgba(0,0,0,1)] relative overflow-hidden min-h-[400px]">
            {/* Screws */}
            <div className="absolute top-2 left-2 w-3 h-3 rounded-full bg-zinc-800 shadow-[inset_1px_1px_2px_rgba(0,0,0,0.8)] flex items-center justify-center"><div className="w-full h-0.5 bg-zinc-900 rotate-45"></div></div>
            <div className="absolute top-2 right-2 w-3 h-3 rounded-full bg-zinc-800 shadow-[inset_1px_1px_2px_rgba(0,0,0,0.8)] flex items-center justify-center"><div className="w-full h-0.5 bg-zinc-900 rotate-45"></div></div>
            <div className="absolute bottom-2 left-2 w-3 h-3 rounded-full bg-zinc-800 shadow-[inset_1px_1px_2px_rgba(0,0,0,0.8)] flex items-center justify-center"><div className="w-full h-0.5 bg-zinc-900 rotate-45"></div></div>
            <div className="absolute bottom-2 right-2 w-3 h-3 rounded-full bg-zinc-800 shadow-[inset_1px_1px_2px_rgba(0,0,0,0.8)] flex items-center justify-center"><div className="w-full h-0.5 bg-zinc-900 rotate-45"></div></div>

            {/* Label */}
            <div className="absolute top-3 left-1/2 -translate-x-1/2 text-zinc-600 font-bold tracking-[0.5em] text-xs border border-zinc-700 px-2 py-0.5 rounded bg-black/30 flex items-center gap-2">
                <Settings2 size={10} /> FREQ_MODULATOR_V2
            </div>

            <motion.div
                className="grid grid-cols-3 gap-y-8 gap-x-4 mt-8"
                initial="hidden"
                animate="visible"
                variants={{
                    visible: { transition: { staggerChildren: 0.05 } }
                }}
            >
                {Object.entries(knobs).map(([name, value], index) => {
                    // Alternate colors for aesthetic
                    const color = index % 2 === 0 ? '#00f3ff' : '#00ff41';
                    return (
                        <motion.div
                            key={name}
                            className="flex justify-center"
                            variants={{
                                hidden: { opacity: 0, y: 20 },
                                visible: { opacity: 1, y: 0 }
                            }}
                            layout // Animate layout changes when items are added
                        >
                            <Knob
                                label={name}
                                value={value}
                                onChange={(val: number) => onUpdate(name, val)}
                                color={color}
                            />
                        </motion.div>
                    );
                })}

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