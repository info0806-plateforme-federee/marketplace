import type { PageServerLoad } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';

export const load: PageServerLoad = async ({ fetch }) => {
	const client = createMarketplaceClient(fetch, env.MARKETPLACE_API_URL ?? 'http://localhost:8090');

	// Get all services (including non-public, all statuses) for current site.
	// The API defaults to showing only active+public; passing undefined filters
	// retrieves everything available to this node.
	const services = await client.getServices({
		status: undefined,
		visibility: undefined,
		per_page: 50
	});

	return { services };
};
