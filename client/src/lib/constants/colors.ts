/**
 * Color theme constants
 * Professional emerald/teal color scheme
 */

export const COLORS = {
	/** Primary accent color - emerald */
	primary: '#10b981',
	primaryDark: '#059669',
	primaryLight: '#34d399',
	
	/** Secondary accent - teal */
	secondary: '#14b8a6',
	secondaryDark: '#0d9488',
	secondaryLight: '#2dd4bf',
	
	/** Hover states */
	hover: '#34d399',
	hoverDark: '#059669',
	
	/** Border colors with opacity */
	border: 'rgba(16, 185, 129, 0.1)',
	borderMedium: 'rgba(16, 185, 129, 0.3)',
	borderStrong: 'rgba(16, 185, 129, 0.5)',
	
	/** Background gradients */
	gradient: {
		primary: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
		secondary: 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)',
		accent: 'linear-gradient(90deg, #10b981, #059669)',
		hover: 'linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.5), transparent)'
	},
	
	/** Shadow colors */
	shadow: 'rgba(16, 185, 129, 0.2)',
	shadowMedium: 'rgba(16, 185, 129, 0.3)',
	shadowStrong: 'rgba(16, 185, 129, 0.5)'
} as const;

