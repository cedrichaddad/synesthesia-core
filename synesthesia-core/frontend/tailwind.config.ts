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
                cyber: {
                    black: '#050505',
                    dark: '#0a0f14',
                    slate: '#1e293b',
                    neon: '#00ff41',
                    cyan: '#00f3ff',
                    warn: '#ffb700',
                    danger: '#ff003c',
                }
            },
            fontFamily: {
                mono: ['"Courier Prime"', 'monospace'],
                tech: ['"Rajdhani"', 'sans-serif'],
            },
        },
    },
    plugins: [],
};
export default config;
