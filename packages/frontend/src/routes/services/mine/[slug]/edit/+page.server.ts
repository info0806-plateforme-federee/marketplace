/**
 * Loader de la page d'édition de service + action de formulaire.
 *
 * `load` récupère le service (y compris privé, via `includePrivate=true`) pour que
 * le propriétaire puisse l'éditer. L'action par défaut construit une mise à jour
 * partielle à partir des seuls champs de formulaire non vides — en parsant les tags
 * (CSV → tableau), les champs de schéma (JSON) et les champs numériques — puis PATCH
 * le service et redirige vers sa page de détail ; les erreurs de validation/d'API
 * sont renvoyées via `fail`.
 */
import type { PageServerLoad, Actions } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';
import { error, fail, redirect } from '@sveltejs/kit';
import { localizeHref } from '$lib/paraglide/runtime';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const client = createMarketplaceClient(fetch, env.MARKETPLACE_API_URL ?? 'http://localhost:8090');

	try {
		const service = await client.getService(params.slug, true);
		return { service };
	} catch {
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

		const updateData: Record<string, unknown> = {};

		for (const [key, value] of formData.entries()) {
			if (value !== '' && value !== null) {
				if (key === 'tags') {
					updateData[key] = (value as string)
						.split(',')
						.map((t) => t.trim())
						.filter(Boolean);
				} else if (key === 'input_schema' || key === 'output_schema') {
					try {
						updateData[key] = JSON.parse(value as string);
					} catch {
						return fail(400, { error: `Invalid JSON in ${key}` });
					}
				} else if (key === 'price_amount' || key === 'max_concurrency' || key === 'timeout_s') {
					updateData[key] = value ? Number(value) : null;
				} else {
					updateData[key] = value;
				}
			}
		}

		try {
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			await client.updateService(params.slug, updateData as any);
			redirect(303, localizeHref(`/services/${params.slug}`));
		} catch (e) {
			if (e instanceof Response || (e as { status?: number })?.status === 303) throw e;
			return fail(500, { error: e instanceof Error ? e.message : 'Failed to update service' });
		}
	}
};
