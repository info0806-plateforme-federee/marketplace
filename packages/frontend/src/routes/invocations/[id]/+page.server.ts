import type { PageServerLoad } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const client = createMarketplaceClient(fetch, env.MARKETPLACE_API_URL ?? 'http://localhost:8090');

	try {
		const invocation = await client.getInvocation(params.id);
		return { invocation };
	} catch {
		error(404, 'Invocation not found');
	}
};
