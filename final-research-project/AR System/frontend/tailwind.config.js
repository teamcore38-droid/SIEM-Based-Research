/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                cyber: {
                    dark: '#050b14',       // Deep space black
                    light: '#1a2333',      // Lighter panel bg
                    accent: '#00f0ff',     // Cyan Neon
                    danger: '#ff003c',     // Red Neon
                    success: '#05ffa1',    // Green Neon
                    warning: '#fcee0a',    // Yellow Neon
                    purple: '#bc13fe',     // Purple Neon
                    muted: '#64748b'
                }
            },
            fontFamily: {
                mono: ['"Fira Code"', 'monospace'],
                display: ['"Rajdhani"', 'sans-serif']
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }
        },
    },
    plugins: [],
}
