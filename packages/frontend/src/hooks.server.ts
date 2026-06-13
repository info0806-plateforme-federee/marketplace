/**
 * Hooks serveur SvelteKit.
 *
 * Enveloppe chaque requête dans le middleware i18n Paraglide : il résout la locale
 * depuis la requête et substitue les marqueurs `%paraglide.lang%`/`%paraglide.dir%`
 * dans app.html pour que la page servie ait les bons `lang`/`dir`.
 */
import type { Handle } from '@sveltejs/kit';
import { getTextDirection } from '$lib/paraglide/runtime';
import { paraglideMiddleware } from '$lib/paraglide/server';

// Fait passer les requêtes par le middleware Paraglide pour fixer locale + direction du texte.
const handleParaglide: Handle = ({ event, resolve }) =>
	paraglideMiddleware(event.request, ({ request, locale }) => {
		event.request = request;

		return resolve(event, {
			transformPageChunk: ({ html }) =>
				html
					.replace('%paraglide.lang%', locale)
					.replace('%paraglide.dir%', getTextDirection(locale))
		});
	});

export const handle: Handle = handleParaglide;
