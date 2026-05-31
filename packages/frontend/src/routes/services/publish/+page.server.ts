import type { PageServerLoad, Actions } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';
import { fail, redirect } from '@sveltejs/kit';
import { localizeHref } from '$lib/paraglide/runtime';

export const load: PageServerLoad = async () => {
	return {};
};

export const actions: Actions = {
	default: async ({ fetch, request }) => {
		const client = createMarketplaceClient(
			fetch,
			env.MARKETPLACE_API_URL ?? 'http://localhost:8090'
		);
		const apiBase = env.MARKETPLACE_API_URL ?? 'http://localhost:8090';
		const formData = await request.formData();

		// --- Service contract fields ---
		const name = formData.get('name') as string;
		const description = formData.get('description') as string;
		const category = formData.get('category') as string;
		const tagsRaw = formData.get('tags') as string;
		const service_type = formData.get('service_type') as string;
		const version = (formData.get('version') as string) || '1.0.0';
		const price_type = formData.get('price_type') as string;
		const price_amount_raw = formData.get('price_amount') as string;
		const currency = (formData.get('currency') as string) || 'EUR';
		const visibility = formData.get('visibility') as string;
		const execution_mode = formData.get('execution_mode') as string;
		const input_schema_raw = formData.get('input_schema') as string;
		const output_schema_raw = formData.get('output_schema') as string;
		const max_concurrency_raw = formData.get('max_concurrency') as string;
		const timeout_s_raw = formData.get('timeout_s') as string;
		const terms_of_use = formData.get('terms_of_use') as string;

		// --- Execution config fields (forwarded to node, not stored in marketplace) ---
		const image = formData.get('image') as string;
		const command = formData.get('command') as string;
		const code = formData.get('code') as string;
		const default_env_raw = formData.get('default_env') as string;
		const default_args_raw = formData.get('default_args') as string;
		const min_cpu_raw = formData.get('min_cpu') as string;
		const min_gpu_raw = formData.get('min_gpu') as string;
		const min_mem_mb_raw = formData.get('min_mem_mb') as string;
		const retry_count_raw = formData.get('retry_count') as string;

		if (!name || !category || !service_type || !price_type || !visibility || !execution_mode) {
			return fail(400, { error: 'Please fill in all required fields' });
		}

		let input_schema = {};
		let output_schema = {};
		let default_env = {};
		let default_args = {};
		try {
			if (input_schema_raw) input_schema = JSON.parse(input_schema_raw);
			if (output_schema_raw) output_schema = JSON.parse(output_schema_raw);
			if (default_env_raw) default_env = JSON.parse(default_env_raw);
			if (default_args_raw) default_args = JSON.parse(default_args_raw);
		} catch {
			return fail(400, { error: 'Invalid JSON in schema fields' });
		}

		const tags = tagsRaw
			? tagsRaw
					.split(',')
					.map((t) => t.trim())
					.filter(Boolean)
			: [];
		const price_amount = price_amount_raw ? Number(price_amount_raw) : null;
		const max_concurrency = max_concurrency_raw ? Number(max_concurrency_raw) : null;
		const timeout_s = timeout_s_raw ? Number(timeout_s_raw) : null;

		try {
			// Step 1: Create the service contract in marketplace
			const service = await client.createService({
				name,
				description: description || undefined,
				category,
				tags,
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				service_type: service_type as any,
				version,
				status: 'active',
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				price_type: price_type as any,
				price_amount,
				currency,
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				visibility: visibility as any,
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				execution_mode: execution_mode as any,
				input_schema,
				output_schema,
				max_concurrency,
				timeout_s,
				terms_of_use: terms_of_use || undefined
			});

			// Step 2: Register execution config on the provider node (via proxy)
			const hasExecConfig = image || code || command;
			if (hasExecConfig) {
				const execConfig: Record<string, unknown> = {};
				if (image) execConfig.image = image;
				if (code) execConfig.code = code;
				if (command) execConfig.command = command;
				if (Object.keys(default_args).length > 0) execConfig.default_args = default_args;
				if (Object.keys(default_env).length > 0) execConfig.default_env = default_env;
				if (min_cpu_raw) execConfig.min_cpu = Number(min_cpu_raw);
				if (min_gpu_raw) execConfig.min_gpu = Number(min_gpu_raw);
				if (min_mem_mb_raw) execConfig.min_mem_mb = Number(min_mem_mb_raw);
				if (retry_count_raw) execConfig.retry_count = Number(retry_count_raw);

				await fetch(`${apiBase}/api/services/${service.slug}/execution-config`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify(execConfig)
				});
			}

			redirect(303, localizeHref(`/services/${service.slug}`));
		} catch (e) {
			if (e instanceof Response || (e as { status?: number })?.status === 303) throw e;
			return fail(500, { error: e instanceof Error ? e.message : 'Failed to create service' });
		}
	}
};
