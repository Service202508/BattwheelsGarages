/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
  	extend: {
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		colors: {
  			/* Battwheels Dark Volt Design System */
  			'bw-black': 'rgb(var(--bw-black) / <alpha-value>)',
  			'bw-off-black': 'rgb(var(--bw-off-black) / <alpha-value>)',
  			'bw-panel': 'rgb(var(--bw-panel) / <alpha-value>)',
  			'bw-card': 'rgb(var(--bw-card) / <alpha-value>)',
  			'bw-volt': 'rgb(var(--bw-volt) / <alpha-value>)',
  			'bw-volt-hover': 'rgb(var(--bw-volt-hover) / <alpha-value>)',
  			'bw-white': 'rgb(var(--bw-white) / <alpha-value>)',
  			'bw-green': 'rgb(var(--bw-green) / <alpha-value>)',
  			'bw-green-hover': 'rgb(var(--bw-green-hover) / <alpha-value>)',
  			'bw-red': 'rgb(var(--bw-red) / <alpha-value>)',
  			'bw-orange': 'rgb(var(--bw-orange) / <alpha-value>)',
  			'bw-amber': 'rgb(var(--bw-amber) / <alpha-value>)',
  			'bw-blue': 'rgb(var(--bw-blue) / <alpha-value>)',
  			'bw-blue-hover': 'rgb(var(--bw-blue-hover) / <alpha-value>)',
  			'bw-teal': 'rgb(var(--bw-teal) / <alpha-value>)',
  			'bw-purple': 'rgb(var(--bw-purple) / <alpha-value>)',
  			/* Shadcn UI tokens */
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			}
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};