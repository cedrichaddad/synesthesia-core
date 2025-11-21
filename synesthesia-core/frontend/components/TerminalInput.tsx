'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Search } from 'lucide-react';
import { Song } from '../types';

interface TerminalInputProps {
    onSearch: (query: string) => void;
    results: Song[];
    onSelect: (song: Song) => void;
    isSearching: boolean;
}

const TerminalInput: React.FC<TerminalInputProps> = ({ onSearch, results, onSelect, isSearching }) => {
    const [value, setValue] = useState('');
    const [isOpen, setIsOpen] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Debounce search
        const timer = setTimeout(() => {
            if (value) onSearch(value);
        }, 400);
        return () => clearTimeout(timer);
    }, [value, onSearch]);

    return (
        <div ref={wrapperRef} className="relative font-mono w-full max-w-md">
            {/* Input Frame */}
            <div className="bg-black border border-cyber-neon/50 p-1 rounded shadow-[0_0_10px_rgba(0,255,65,0.1)]">
                <div className="flex items-center gap-2 px-3 py-2 bg-cyber-dark">
                    <span className="text-cyber-neon text-sm animate-pulse">{'>'}</span>
                    <input
                        type="text"
                        value={value}
                        onChange={(e) => {
                            setValue(e.target.value);
                            setIsOpen(true);
                        }}
                        onFocus={() => setIsOpen(true)}
                        placeholder="QUERY_DATABASE..."
                        className="w-full bg-transparent text-cyber-neon placeholder-cyber-neon/30 focus:outline-none uppercase tracking-wider text-sm"
                        autoComplete="off"
                    />
                    {isSearching && <Search size={16} className="text-cyber-neon animate-spin" />}
                </div>
            </div>

            {/* Dropdown "System Log" */}
            {isOpen && results.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-black/95 border border-cyber-neon/30 backdrop-blur-md z-50 max-h-60 overflow-y-auto scrollbar-hide">
                    <div className="text-[10px] text-gray-500 bg-gray-900 px-2 py-1 border-b border-gray-800 sticky top-0">
                        FOUND {results.length} RECORDS...
                    </div>
                    {results.map((song) => (
                        <button
                            key={song.id}
                            onClick={() => {
                                onSelect(song);
                                setIsOpen(false);
                                setValue('');
                            }}
                            className="w-full text-left px-4 py-2 text-xs md:text-sm text-cyber-neon hover:bg-cyber-neon/10 hover:pl-6 transition-all duration-200 border-b border-cyber-neon/10 flex justify-between items-center group"
                        >
                            <span>{song.title} {'//'} {song.artist}</span>
                            <span className="opacity-0 group-hover:opacity-100 text-[10px]">LOAD_PROGRAM</span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

export default TerminalInput;