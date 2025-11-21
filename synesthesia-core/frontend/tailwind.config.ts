import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "var(--background)",
                foreground: "var(--foreground)",
                cyber: {
                    black: '#050505',
                    dark: '#0a0f14',
                    slate: '#1e293b',
                    neon: '#00ff41',
                    cyan: '#00f3ff',
                    warn: '#ffb700',
                    danger: '#ff003c',
                    glass: 'rgba(10, 15, 20, 0.6)',
                }
            },
            fontFamily: {
                mono: ['"Courier Prime"', 'monospace'],
                tech: ['"Rajdhani"', 'sans-serif'],
            },
            backgroundImage: {
                'hex-pattern': "url('https://www.transparenttextures.com/patterns/carbon-fibre.png')",
            },
            animation: {
                'scanline': 'scanline 8s linear infinite',
                'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
            },
            keyframes: {
                scanline: {
                    '0%': { backgroundPosition: '0% 0%' },
                    '100%': { backgroundPosition: '0% 100%' },
                },
                glow: {
                    'from': { boxShadow: '0 0 10px #00f3ff, 0 0 20px #00f3ff' },
                    'to': { boxShadow: '0 0 20px #00f3ff, 0 0 30px #00f3ff' },
                }
            }
        },
    },
    plugins: [],
};
export default config;
