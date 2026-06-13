/**
 * Store global de thème clair/sombre (runes Svelte 5).
 *
 * Détient l'état réactif `dark`, initialisé depuis `localStorage` (avec repli sur
 * le `prefers-color-scheme` de l'OS) et reflété sur la classe `dark` de l'élément
 * `<html>`. `toggle()` l'inverse et persiste le choix. Exporté comme une unique
 * instance `theme` partagée.
 */
import { browser } from '$app/environment';

// ---------------------------------------------------------------------------
// État du thème
// ---------------------------------------------------------------------------

/**
 * Construit le store de thème : résout la valeur initiale côté client et expose un
 * getter réactif `dark` plus un `toggle()` qui met à jour le DOM et le stockage.
 */
function createTheme() {
	let dark = $state(false);

	if (browser) {
		const stored = localStorage.getItem('theme');
		dark = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
		// Applique la classe de façon synchrone avant le premier rendu pour éviter le flash.
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
