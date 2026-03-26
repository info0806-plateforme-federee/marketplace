<script lang="ts">
	import * as m from '$lib/paraglide/messages';
	import { localizeHref } from '$lib/paraglide/runtime';
	import { enhance } from '$app/forms';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Textarea from '$lib/components/ui/Textarea.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import Card from '$lib/components/ui/Card.svelte';

	let { form } = $props();

	const serviceTypes = [
		{ value: 'compute', label: m.type_compute() },
		{ value: 'data', label: m.type_data() },
		{ value: 'model', label: m.type_model() },
		{ value: 'utility', label: m.type_utility() }
	];

	const priceTypes = [
		{ value: 'free', label: m.price_free() },
		{ value: 'fixed', label: 'Fixed per call' },
		{ value: 'time', label: 'Time-based' }
	];

	const visibilityOptions = [
		{ value: 'public', label: m.visibility_public() },
		{ value: 'private', label: m.visibility_private() },
		{ value: 'restricted', label: m.visibility_restricted() }
	];

	const executionModes = [
		{ value: 'sync', label: m.mode_sync() },
		{ value: 'async', label: m.mode_async() }
	];
</script>

<svelte:head>
	<title>{m.publish_title()}</title>
</svelte:head>

<PageHeader title={m.publish_title()} subtitle={m.publish_subtitle()}>
	{#snippet actions()}
		<Button variant="outline" href={localizeHref('/services')}>{m.common_back()}</Button>
	{/snippet}
</PageHeader>

<Card>
	{#if form?.error}
		<div
			class="mb-4 rounded-md bg-red-100 p-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-400"
		>
			{form.error}
		</div>
	{/if}

	<form method="POST" use:enhance class="space-y-6">
		<!-- Basic Info -->
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<Input name="name" label={m.publish_name()} required />
			<Input
				name="category"
				label={m.publish_category()}
				required
				placeholder="ml, data, compute..."
			/>
		</div>

		<Textarea name="description" label={m.publish_description()} rows={3} />
		<Input name="tags" label={m.publish_tags()} placeholder={m.publish_tags_hint()} />

		<!-- Type & Version -->
		<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
			<Select name="service_type" label={m.publish_type()} options={serviceTypes} required />
			<Input name="version" label={m.publish_version()} value="1.0.0" />
			<Select
				name="execution_mode"
				label={m.publish_execution()}
				options={executionModes}
				required
			/>
		</div>

		<!-- Pricing -->
		<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
			<Select name="price_type" label={m.publish_pricing()} options={priceTypes} required />
			<Input
				name="price_amount"
				label={m.publish_price_amount()}
				type="number"
				placeholder="0.00"
			/>
			<Input name="currency" label={m.publish_currency()} value="EUR" />
		</div>

		<!-- Visibility -->
		<Select name="visibility" label={m.publish_visibility()} options={visibilityOptions} required />

		<!-- Schemas -->
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<Textarea name="input_schema" label={m.publish_input_schema()} rows={6} />
			<Textarea name="output_schema" label={m.publish_output_schema()} rows={6} />
		</div>

		<!-- Advanced -->
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<Input name="max_concurrency" label={m.publish_max_concurrency()} type="number" />
			<Input name="timeout_s" label={m.publish_timeout()} type="number" />
		</div>

		<Textarea name="terms_of_use" label={m.publish_terms()} rows={3} />

		<div class="flex gap-3">
			<Button type="submit">{m.publish_submit()}</Button>
			<Button variant="outline" href={localizeHref('/services')}>{m.common_cancel()}</Button>
		</div>
	</form>
</Card>
