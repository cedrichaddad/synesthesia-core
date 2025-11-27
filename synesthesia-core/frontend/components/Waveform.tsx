'use client';

import React, { useEffect, useRef } from 'react';

interface WaveformProps {
    audioUrl: string | null;
    isPlaying: boolean;
}

const Waveform: React.FC<WaveformProps> = ({ audioUrl, isPlaying }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const animationFrameRef = useRef<number>(undefined);

    useEffect(() => {
        if (!audioUrl) return;

        // Initialize Audio Context
        if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        }

        const ctx = audioContextRef.current;
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 2048;
        analyserRef.current = analyser;

        // Create Audio Element
        const audio = new Audio(audioUrl);
        audio.crossOrigin = "anonymous";
        audioRef.current = audio;

        // Connect Source
        const source = ctx.createMediaElementSource(audio);
        source.connect(analyser);
        analyser.connect(ctx.destination);
        sourceRef.current = source;

        return () => {
            audio.pause();
            source.disconnect();
            // Don't close context to allow reuse, or manage lifecycle carefully
        };
    }, [audioUrl]);

    useEffect(() => {
        if (isPlaying && audioRef.current) {
            audioContextRef.current?.resume();
            audioRef.current.play().catch(e => console.error("Playback failed:", e));
            draw();
        } else if (audioRef.current) {
            audioRef.current.pause();
            cancelAnimationFrame(animationFrameRef.current!);
        }
    }, [isPlaying]);

    const draw = () => {
        if (!canvasRef.current || !analyserRef.current) return;

        const canvas = canvasRef.current;
        const canvasCtx = canvas.getContext('2d');
        if (!canvasCtx) return;

        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const render = () => {
            animationFrameRef.current = requestAnimationFrame(render);
            analyserRef.current!.getByteTimeDomainData(dataArray);

            canvasCtx.fillStyle = 'rgba(10, 10, 15, 0.2)'; // Fade effect
            canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

            canvasCtx.lineWidth = 2;
            canvasCtx.strokeStyle = '#00f3ff'; // Cyan
            canvasCtx.beginPath();

            const sliceWidth = canvas.width * 1.0 / bufferLength;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * canvas.height / 2;

                if (i === 0) {
                    canvasCtx.moveTo(x, y);
                } else {
                    canvasCtx.lineTo(x, y);
                }

                x += sliceWidth;
            }

            canvasCtx.lineTo(canvas.width, canvas.height / 2);
            canvasCtx.stroke();
        };

        render();
    };

    return (
        <div className="w-full h-32 bg-black/90 border border-cyber-slate/50 rounded-sm relative overflow-hidden shadow-[0_0_15px_rgba(0,243,255,0.1)]">
            <canvas
                ref={canvasRef}
                width={600}
                height={128}
                className="w-full h-full"
            />
            {/* Grid Overlay */}
            <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:20px_20px] pointer-events-none"></div>

            <div className="absolute top-2 left-2 text-[10px] text-cyber-blue font-mono tracking-widest opacity-70">
                OSCILLOSCOPE // INPUT_GAIN: +3dB
            </div>
        </div>
    );
};

export default Waveform;
