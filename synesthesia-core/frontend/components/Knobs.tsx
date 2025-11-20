"use client";

import React, { useState } from 'react';

interface KnobProps {
    label: string;
    onChange: (value: float) => void;
}

const Knob: React.FC<KnobProps> = ({ label, onChange }) => {
    const [value, setValue] = useState(0);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = parseFloat(e.target.value);
        setValue(val);
        onChange(val);
    };

    return (
        <div className="flex flex-col items-center space-y-2">
            <label className="text-white font-mono text-sm">{label}</label>
            <input
                type="range"
                min="-1.0"
                max="1.0"
                step="0.1"
                value={value}
                onChange={handleChange}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <span className="text-xs text-gray-400">{value.toFixed(1)}</span>
        </div>
    );
};

export default function Knobs() {
    const handleKnobChange = (knob: string, value: number) => {
        console.log(`Knob ${knob} changed to ${value}`);
        // Call API here
    };

    return (
        <div className="grid grid-cols-3 gap-4 p-4 bg-gray-900 rounded-lg border border-gray-800">
            <Knob label="Drums" onChange={(v) => handleKnobChange("Drums", v)} />
            <Knob label="Vocals" onChange={(v) => handleKnobChange("Vocals", v)} />
            <Knob label="Synth" onChange={(v) => handleKnobChange("Synth", v)} />
            <Knob label="Tempo" onChange={(v) => handleKnobChange("Tempo", v)} />
            <Knob label="Dark" onChange={(v) => handleKnobChange("Dark", v)} />
            <Knob label="Happy" onChange={(v) => handleKnobChange("Happy", v)} />
        </div>
    );
}
