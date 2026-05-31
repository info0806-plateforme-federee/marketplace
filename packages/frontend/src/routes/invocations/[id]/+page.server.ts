import type { PageServerLoad } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env as privateEnv } from '$env/dynamic/private';
import { env as publicEnv } from '$env/dynamic/public';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ fetch, params, url }) => {
	const apiUrl = privateEnv.MARKETPLACE_API_URL ?? 'http://localhost:8090';
	const client = createMarketplaceClient(fetch, apiUrl);

	try {
		const invocation = await client.getInvocation(params.id);
		const publicApiUrl =
			publicEnv.PUBLIC_MARKETPLACE_API_URL ?? `${url.protocol}//${url.hostname}:8090`;
		const wsUrl = new URL(`/api/invocations/${params.id}/ws`, publicApiUrl);
		wsUrl.protocol = wsUrl.protocol === 'https:' ? 'wss:' : 'ws:';
		return { invocation, wsUrl: wsUrl.toString(), apiBaseUrl: publicApiUrl };
	} catch {
		error(404, 'Invocation not found');
	}
};
