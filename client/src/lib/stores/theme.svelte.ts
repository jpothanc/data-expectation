/**
 * Theme store for managing application themes
 */

export interface Theme {
	id: string;
	name: string;
	colors: {
		primary: string;
		primaryDark: string;
		primaryLight: string;
		secondary?: string;
		hover: string;
		border: string;
		borderMedium: string;
		borderStrong: string;
		gradient: {
			primary: string;
			secondary: string;
			accent: string;
			hover: string;
		};
		shadow: string;
		shadowMedium: string;
		shadowStrong: string;
	};
}

export const themes: Theme[] = [
	{
		id: 'emerald',
		name: 'Emerald',
		colors: {
			primary: '#10b981',
			primaryDark: '#059669',
			primaryLight: '#34d399',
			secondary: '#14b8a6',
			hover: '#34d399',
			border: 'rgba(16, 185, 129, 0.1)',
			borderMedium: 'rgba(16, 185, 129, 0.3)',
			borderStrong: 'rgba(16, 185, 129, 0.5)',
			gradient: {
				primary: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
				secondary: 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)',
				accent: 'linear-gradient(90deg, #10b981, #059669)',
				hover: 'linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.5), transparent)'
			},
			shadow: 'rgba(16, 185, 129, 0.2)',
			shadowMedium: 'rgba(16, 185, 129, 0.3)',
			shadowStrong: 'rgba(16, 185, 129, 0.5)'
		}
	},
	{
		id: 'blue',
		name: 'Blue',
		colors: {
			primary: '#3b82f6',
			primaryDark: '#2563eb',
			primaryLight: '#60a5fa',
			secondary: '#0ea5e9',
			hover: '#60a5fa',
			border: 'rgba(96, 165, 250, 0.1)',
			borderMedium: 'rgba(96, 165, 250, 0.3)',
			borderStrong: 'rgba(96, 165, 250, 0.5)',
			gradient: {
				primary: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
				secondary: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
				accent: 'linear-gradient(90deg, #60a5fa, #3b82f6)',
				hover: 'linear-gradient(90deg, transparent, rgba(96, 165, 250, 0.5), transparent)'
			},
			shadow: 'rgba(96, 165, 250, 0.2)',
			shadowMedium: 'rgba(37, 99, 235, 0.3)',
			shadowStrong: 'rgba(96, 165, 250, 0.5)'
		}
	},
	{
		id: 'purple',
		name: 'Purple',
		colors: {
			primary: '#8b5cf6',
			primaryDark: '#7c3aed',
			primaryLight: '#a78bfa',
			secondary: '#a855f7',
			hover: '#a78bfa',
			border: 'rgba(139, 92, 246, 0.1)',
			borderMedium: 'rgba(139, 92, 246, 0.3)',
			borderStrong: 'rgba(139, 92, 246, 0.5)',
			gradient: {
				primary: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
				secondary: 'linear-gradient(135deg, #a855f7 0%, #9333ea 100%)',
				accent: 'linear-gradient(90deg, #a78bfa, #8b5cf6)',
				hover: 'linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.5), transparent)'
			},
			shadow: 'rgba(139, 92, 246, 0.2)',
			shadowMedium: 'rgba(124, 58, 237, 0.3)',
			shadowStrong: 'rgba(139, 92, 246, 0.5)'
		}
	},
	{
		id: 'amber',
		name: 'Amber',
		colors: {
			primary: '#f59e0b',
			primaryDark: '#d97706',
			primaryLight: '#fbbf24',
			secondary: '#f97316',
			hover: '#fbbf24',
			border: 'rgba(245, 158, 11, 0.1)',
			borderMedium: 'rgba(245, 158, 11, 0.3)',
			borderStrong: 'rgba(245, 158, 11, 0.5)',
			gradient: {
				primary: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
				secondary: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
				accent: 'linear-gradient(90deg, #fbbf24, #f59e0b)',
				hover: 'linear-gradient(90deg, transparent, rgba(245, 158, 11, 0.5), transparent)'
			},
			shadow: 'rgba(245, 158, 11, 0.2)',
			shadowMedium: 'rgba(217, 119, 6, 0.3)',
			shadowStrong: 'rgba(245, 158, 11, 0.5)'
		}
	},
	{
		id: 'cyan',
		name: 'Cyan',
		colors: {
			primary: '#06b6d4',
			primaryDark: '#0891b2',
			primaryLight: '#22d3ee',
			secondary: '#14b8a6',
			hover: '#22d3ee',
			border: 'rgba(6, 182, 212, 0.1)',
			borderMedium: 'rgba(6, 182, 212, 0.3)',
			borderStrong: 'rgba(6, 182, 212, 0.5)',
			gradient: {
				primary: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
				secondary: 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)',
				accent: 'linear-gradient(90deg, #22d3ee, #06b6d4)',
				hover: 'linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.5), transparent)'
			},
			shadow: 'rgba(6, 182, 212, 0.2)',
			shadowMedium: 'rgba(8, 145, 178, 0.3)',
			shadowStrong: 'rgba(6, 182, 212, 0.5)'
		}
	}
];

const THEME_STORAGE_KEY = 'app-theme';
const DEFAULT_THEME_ID = 'emerald';

class ThemeStore {
	private _currentTheme = $state<Theme>(themes.find(t => t.id === DEFAULT_THEME_ID) || themes[0]);
	private _initialized = false;
	
	constructor() {
		// Don't initialize here - wait for browser context via initialize() method
	}
	
	initialize() {
		if (this._initialized) return;
		this._initialized = true;
		
		if (typeof window === 'undefined') return;
		
		const savedThemeId = localStorage.getItem(THEME_STORAGE_KEY);
		if (savedThemeId) {
			const savedTheme = themes.find(t => t.id === savedThemeId);
			if (savedTheme) {
				this._currentTheme = savedTheme;
				this.applyTheme(savedTheme);
				return;
			}
		}
		this.applyTheme(this._currentTheme);
	}
	
	get currentTheme() {
		return this._currentTheme;
	}
	
	setTheme(themeId: string) {
		const theme = themes.find(t => t.id === themeId);
		if (theme) {
			this._currentTheme = theme;
			this.applyTheme(theme);
			if (typeof window !== 'undefined') {
				localStorage.setItem(THEME_STORAGE_KEY, themeId);
			}
		}
	}
	
	private applyTheme(theme: Theme) {
		if (typeof document === 'undefined') return;
		
		const root = document.documentElement;
		root.style.setProperty('--color-primary', theme.colors.primary);
		root.style.setProperty('--color-primary-dark', theme.colors.primaryDark);
		root.style.setProperty('--color-primary-light', theme.colors.primaryLight);
		root.style.setProperty('--color-secondary', theme.colors.secondary || theme.colors.primary);
		root.style.setProperty('--color-hover', theme.colors.hover);
		root.style.setProperty('--color-border', theme.colors.border);
		root.style.setProperty('--color-border-medium', theme.colors.borderMedium);
		root.style.setProperty('--color-border-strong', theme.colors.borderStrong);
		root.style.setProperty('--gradient-primary', theme.colors.gradient.primary);
		root.style.setProperty('--gradient-secondary', theme.colors.gradient.secondary);
		root.style.setProperty('--gradient-accent', theme.colors.gradient.accent);
		root.style.setProperty('--gradient-hover', theme.colors.gradient.hover);
		root.style.setProperty('--shadow-primary', theme.colors.shadow);
		root.style.setProperty('--shadow-medium', theme.colors.shadowMedium);
		root.style.setProperty('--shadow-strong', theme.colors.shadowStrong);
	}
}

export const themeStore = new ThemeStore();

