/**
 * Color replacement utility
 * This file documents the color theme migration from blue to emerald/teal
 * 
 * Color Mapping:
 * #60a5fa (blue-400) -> #34d399 (emerald-400) - lighter accents
 * #3b82f6 (blue-500) -> #10b981 (emerald-500) - primary color
 * #2563eb (blue-600) -> #059669 (emerald-600) - darker accents
 * rgba(96, 165, 250, x) -> rgba(16, 185, 129, x) - primary with opacity
 * rgba(96, 165, 250, x) -> rgba(52, 211, 153, x) - lighter with opacity (for borders/highlights)
 */

export const COLOR_REPLACEMENTS = {
	// Hex colors
	'#60a5fa': '#34d399', // blue-400 -> emerald-400
	'#3b82f6': '#10b981', // blue-500 -> emerald-500
	'#2563eb': '#059669', // blue-600 -> emerald-600
	
	// RGBA colors - primary
	'rgba(96, 165, 250, 0.1)': 'rgba(16, 185, 129, 0.1)',
	'rgba(96, 165, 250, 0.2)': 'rgba(16, 185, 129, 0.2)',
	'rgba(96, 165, 250, 0.3)': 'rgba(16, 185, 129, 0.3)',
	'rgba(96, 165, 250, 0.5)': 'rgba(16, 185, 129, 0.5)',
	'rgba(96, 165, 250, 0.6)': 'rgba(16, 185, 129, 0.6)',
	
	// RGBA colors - lighter (for highlights/borders)
	'rgba(96, 165, 250, 0.08)': 'rgba(52, 211, 153, 0.08)',
	
	// Box shadows
	'rgba(37, 99, 235, 0.3)': 'rgba(5, 150, 105, 0.3)', // blue-600 shadow -> emerald-600 shadow
} as const;

