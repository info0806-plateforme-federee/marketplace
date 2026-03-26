import type { PageServerLoad } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';
import type { InvocationStatus } from '$lib/types/marketplace';

export const load: PageServerLoad = async ({ fetch, url }) => {
	const client = createMarketplaceClient(fetch, env.MARKETPLACE_API_URL ?? 'http://localhost:8090');

	const statusParam = url.searchParams.get('status') || undefined;
	const invocations = await client.getInvocations({
		status: statusParam as InvocationStatus | undefined,
		page: Number(url.searchParams.get('page')) || 1,
		per_page: 20
	});

	return { invocations };
};
