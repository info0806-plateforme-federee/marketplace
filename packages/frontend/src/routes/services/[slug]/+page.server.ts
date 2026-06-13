/**
 * Loader de la page de détail d'un service.
 *
 * Charge un service public par son slug, ou lève une 404 s'il n'existe pas.
 */
import type { PageServerLoad } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';
import { error } from '@sveltejs/kit';

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
