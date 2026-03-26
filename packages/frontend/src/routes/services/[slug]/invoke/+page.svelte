<script lang="ts">
	import * as m from '$lib/paraglide/messages';
	import { localizeHref } from '$lib/paraglide/runtime';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Textarea from '$lib/components/ui/Textarea.svelte';
	import SchemaViewer from '$lib/components/marketplace/SchemaViewer.svelte';
	import PriceBadge from '$lib/components/marketplace/PriceBadge.svelte';
	import { enhance } from '$app/forms';

	let { data, form } = $props();
	let service = $derived(data.service);

	// Pre-fill the textarea with a JSON template derived from the input schema.
	let defaultPayload = $derived(
		JSON.stringify(
			Object.fromEntries(
				Object.entries(service.input_schema).map(([key, type]) => [
					key,
					type === 'integer' || type === 'number' ? 0 : '',
				])
			),
			null,
			2
		)
	);

	const jsonPlaceholder = '{"key": "value"}';
</script>

<svelte:head>
	<title>{m.invoke_title({ service: service.name })}</title>
</svelte:head>

<PageHeader title={m.invoke_title({ service: service.name })} subtitle={m.invoke_subtitle()}>
	{#snippet actions()}
		<Button variant="outline" href={localizeHref(`/services/${service.slug}`)}>
			{m.common_back()}
		</Button>
	{/snippet}
</PageHeader>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
	<div class="lg:col-span-2">
		<Card>
			{#if form?.error}
				<div
					class="mb-4 p-3 rounded-md bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 text-sm"
				>
					{form.error}
				</div>
			{/if}

			<form method="POST" use:enhance>
				<Textarea
					name="input_payload"
					label={m.invoke_input_payload()}
					value={defaultPayload}
					rows={12}
					placeholder={jsonPlaceholder}
				/>
				<div class="mt-4 flex gap-3">
					<Button type="submit">{m.invoke_submit()}</Button>
					<Button variant="outline" href={localizeHref(`/services/${service.slug}`)}>
						{m.common_cancel()}
					</Button>
				</div>
			</form>
		</Card>
	</div>

	<div class="space-y-6">
		<Card>
			<h3 class="text-sm font-semibold text-foreground mb-2">{m.service_pricing()}</h3>
			<PriceBadge
				priceType={service.price_type}
				priceAmount={service.price_amount}
				currency={service.currency}
			/>
		</Card>

		<Card>
			<SchemaViewer schema={service.input_schema} title={m.service_input_schema()} />
		</Card>

		<Card>
			<SchemaViewer schema={service.output_schema} title={m.service_output_schema()} />
		</Card>
	</div>
</div>
