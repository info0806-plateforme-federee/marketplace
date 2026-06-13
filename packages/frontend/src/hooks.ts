/**
 * Hooks universels SvelteKit (exécutés côté serveur et côté client).
 *
 * `reroute` retire le préfixe de locale des URLs entrantes pour que les chemins
 * localisés (p. ex. `/fr/services`) pointent vers la même route que leur
 * équivalent sans préfixe.
 */
import { deLocalizeUrl } from '$lib/paraglide/runtime';

export const reroute = (request) => deLocalizeUrl(request.url).pathname;
