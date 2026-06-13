/**
 * Loader de la page d'invocation de service + action de formulaire.
 *
 * `load` récupère le service à invoquer (404 si absent). L'action de formulaire par
 * défaut parse le `input_payload` JSON, appelle l'endpoint d'invocation, et en cas
 * de succès redirige vers la page de détail de la nouvelle invocation ; les erreurs
 * JSON ou d'API sont renvoyées à la page pour affichage.
 */
import type { PageServerLoad, Actions } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';
import { error, redirect } from '@sveltejs/kit';
import { localizeHref } from '$lib/paraglide/runtime';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const client = createMarketplaceClient(
		fetch,
		env.MARKETPLACE_API_URL ?? 'http://localhost:8090'
	);

	try {
		const service = await client.getService(params.slug);
		return { service };
	} catch (e) {
		error(404, 'Service not found');
	}
};

export const actions: Actions = {
	default: async ({ fetch, params, request }) => {
		const client = createMarketplaceClient(
			fetch,
			env.MARKETPLACE_API_URL ?? 'http://localhost:8090'
		);
		const formData = await request.formData();
		const inputPayloadRaw = formData.get('input_payload') as string;

		let input_payload: Record<string, unknown> = {};
		try {
			input_payload = JSON.parse(inputPayloadRaw || '{}');
		} catch {
			return { error: 'Invalid JSON in input payload' };
		}

		try {
			const invocation = await client.invokeService(params.slug, { input_payload });
			redirect(303, localizeHref(`/invocations/${invocation.id}`));
		} catch (e) {
			// Relance les réponses redirect/error de SvelteKit (elles sont levées en interne).
			if (
				e instanceof Response ||
				(e as { status?: number })?.status === 303
			) {
				throw e;
			}
			return { error: e instanceof Error ? e.message : 'Failed to invoke service' };
		}
	},
};
