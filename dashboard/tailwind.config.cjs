/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                green: {
                    500: '#22c55e',
                },
                red: {
                    500: '#ef4444',
                },
                yellow: {
                    500: '#facc15',
                },
            },
        },
    },
    plugins: [],
}
