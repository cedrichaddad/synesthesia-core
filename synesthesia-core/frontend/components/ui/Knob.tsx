'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface KnobProps {
    label: string;
    value: number; // 0-100
    onChange: (val: number) => void;
    color?: string;
}

const Knob: React.FC<KnobProps> = ({ label, value, onChange, color = '#00f3ff' }) => {
    const [isDragging, setIsDragging] = useState(false);
    const startY = useRef<number>(0);
    const startValue = useRef<number>(0);

    // Map 0-100 to -135deg to 135deg
    const rotation = (value / 100) * 270 - 135;

    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true);
        startY.current = e.clientY;
        startValue.current = value;
        document.body.style.cursor = 'grabbing';
    };

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isDragging) return;
            const dy = startY.current - e.clientY; // Drag up to increase
            const sensitivity = 1; // Pixels per unit
            let newValue = startValue.current + dy * sensitivity;
            newValue = Math.max(0, Math.min(100, newValue));
            onChange(newValue);
        };

        const handleMouseUp = () => {
            setIsDragging(false);
            document.body.style.cursor = 'default';
        };

        if (isDragging) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        }

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, onChange]);

    return (
        <div className="flex flex-col items-center gap-2 select-none group relative">
            <div className="relative w-20 h-20 flex items-center justify-center">
                {/* Backplate (Holographic Ring) */}
                <div className="absolute inset-0 rounded-full bg-cyber-black/40 shadow-[0_0_15px_rgba(0,243,255,0.05)] border border-cyber-cyan/20 backdrop-blur-sm"></div>

                {/* Ticks */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100">
                    {Array.from({ length: 21 }).map((_, i) => {
                        const angle = -135 + (i * (270 / 20));
                        const isActive = angle <= rotation;
                        return (
                            <line
                                key={i}
                                x1="50" y1="50"
                                x2="50" y2="10"
                                stroke={isActive ? color : 'rgba(255,255,255,0.1)'}
                                strokeWidth={isActive ? "2.5" : "1.5"}
                                transform={`rotate(${angle} 50 50) translate(0, 4)`}
                                strokeLinecap="round"
                                className="transition-colors duration-100"
                                style={{ filter: isActive ? `drop-shadow(0 0 2px ${color})` : 'none' }}
                            />
                        );
                    })}
                </svg>

                {/* The Knob Itself */}
                <motion.div
                    className="relative w-12 h-12 rounded-full cursor-grab active:cursor-grabbing z-10"
                    style={{
                        background: 'radial-gradient(circle at 30% 30%, #2a2a2a, #000000)',
                        transform: `rotate(${rotation}deg)`,
                        boxShadow: isDragging
                            ? `0 0 20px ${color}40, inset 0 0 10px rgba(255,255,255,0.1)`
                            : `0 4px 10px rgba(0,0,0,0.8), inset 0 0 5px rgba(255,255,255,0.05)`
                    }}
                    onMouseDown={handleMouseDown}
                >
                    {/* Indicator Line (Laser) */}
                    <motion.div
                        className="absolute top-1 left-1/2 -translate-x-1/2 w-0.5 h-4 rounded-full bg-white"
                        style={{
                            backgroundColor: color,
                            boxShadow: `0 0 10px ${color}, 0 0 5px white`
                        }}
                    ></motion.div>

                    {/* Center Cap (Lens) */}
                    <div className="absolute inset-4 rounded-full bg-black shadow-[inset_0_1px_2px_rgba(255,255,255,0.2)]"></div>
                </motion.div>
            </div>

            {/* Label */}
            <div className="text-center z-10">
                <div className="text-[10px] font-mono text-slate-400 tracking-widest uppercase mb-0.5">{label}</div>
                <div
                    className="text-xs font-tech font-bold tracking-wider"
                    style={{ color: isDragging ? color : '#64748b' }}
                >
                    {Math.round(value).toString().padStart(3, '0')}
                </div>
            </div>
        </div>
    );
};

export default Knob;