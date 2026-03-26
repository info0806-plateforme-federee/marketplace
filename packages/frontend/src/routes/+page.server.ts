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
			// These are approximations for now, can be enhanced later
			totalInvocations: 0,
			activeSites: 0,
			categories: [...new Set(services.items.map((s) => s.category))].length,
		},
	};
};
