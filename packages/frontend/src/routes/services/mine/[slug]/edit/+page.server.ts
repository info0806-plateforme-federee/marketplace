import type { PageServerLoad, Actions } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';
import { error, fail, redirect } from '@sveltejs/kit';
import { localizeHref } from '$lib/paraglide/runtime';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const client = createMarketplaceClient(fetch, env.MARKETPLACE_API_URL ?? 'http://localhost:8090');

	try {
		const service = await client.getService(params.slug);
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
				} else if (key === 'input_schema' || key === 'output_schema' || key === 'default_env' || key === 'default_args') {
					try {
						updateData[key] = JSON.parse(value as string);
					} catch {
						return fail(400, { error: `Invalid JSON in ${key}` });
					}
				} else if (key === 'price_amount' || key === 'max_concurrency' || key === 'timeout_s' || key === 'min_cpu' || key === 'min_gpu' || key === 'min_mem_mb' || key === 'retry_count') {
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
