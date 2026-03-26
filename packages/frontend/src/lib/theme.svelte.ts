import { browser } from '$app/environment';

// ---------------------------------------------------------------------------
// Theme state
// ---------------------------------------------------------------------------

function createTheme() {
	let dark = $state(false);

	if (browser) {
		const stored = localStorage.getItem('theme');
		dark = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
		// Synchronously apply the class before the first paint to avoid flash.
		document.documentElement.classList.toggle('dark', dark);
	}

	return {
		get dark(): boolean {
			return dark;
		},

		toggle(): void {
			dark = !dark;
			if (browser) {
				document.documentElement.classList.toggle('dark', dark);
				localStorage.setItem('theme', dark ? 'dark' : 'light');
			}
		},
	};
}

export const theme = createTheme();
