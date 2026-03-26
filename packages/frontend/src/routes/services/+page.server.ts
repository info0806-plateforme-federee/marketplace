import type { PageServerLoad } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';
import type { ServiceType, PriceType } from '$lib/types/marketplace';

export const load: PageServerLoad = async ({ fetch, url }) => {
	const client = createMarketplaceClient(fetch, env.MARKETPLACE_API_URL ?? 'http://localhost:8090');

	const filters = {
		search: url.searchParams.get('search') || undefined,
		category: url.searchParams.get('category') || undefined,
		service_type: (url.searchParams.get('service_type') as ServiceType) || undefined,
		price_type: (url.searchParams.get('price_type') as PriceType) || undefined,
		page: Number(url.searchParams.get('page')) || 1,
		per_page: 12,
	};

	const services = await client.getServices(filters);

	return { services };
};
