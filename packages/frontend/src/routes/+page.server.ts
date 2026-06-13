/**
 * Loader de la page d'accueil.
 *
 * Récupère un petit ensemble de services à mettre en avant sur la page d'accueil
 * plus des statistiques de tête. S'exécute côté serveur pour pouvoir lire le
 * `MARKETPLACE_API_URL` privé.
 */
import type { PageServerLoad } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';

export const load: PageServerLoad = async ({ fetch }) => {
	const client = createMarketplaceClient(fetch, env.MARKETPLACE_API_URL ?? 'http://localhost:8090');

	const services = await client.getServices({ per_page: 6 });

	return {
		featuredServices: services.items,
		stats: {
			totalServices: services.total,
			// Ce sont des approximations pour l'instant, à améliorer plus tard
			totalInvocations: 0,
			activeSites: 0,
			categories: [...new Set(services.items.map((s) => s.category))].length,
		},
	};
};
