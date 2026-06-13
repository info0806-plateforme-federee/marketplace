<!--
@component
Formulaire d'édition de service. Contrairement à l'assistant de publication
multi-étapes, c'est un unique formulaire à plat dont les champs sont pré-remplis
depuis le `service` chargé (schémas affichés en JSON formaté). La soumission POST
vers l'action de cette route, qui construit une mise à jour partielle à partir des
champs non vides ; `form.error` fait remonter les échecs.
-->
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

	let { data, form } = $props();
	let service = $derived(data.service);

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
	const statusOptions = [
		{ value: 'active', label: m.status_active() },
		{ value: 'draft', label: m.status_draft() },
		{ value: 'disabled', label: m.status_disabled() },
		{ value: 'deprecated', label: m.status_deprecated() }
	];
</script>

<svelte:head>
	<title>{m.edit_title()}</title>
</svelte:head>

<PageHeader title={m.edit_title()} subtitle={m.edit_subtitle()}>
	{#snippet actions()}
		<Button variant="outline" href={localizeHref(`/services/${service.slug}`)}
			>{m.common_back()}</Button
		>
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
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<Input name="name" label={m.publish_name()} value={service.name} required />
			<Input name="category" label={m.publish_category()} value={service.category} required />
		</div>

		<Textarea
			name="description"
			label={m.publish_description()}
			value={service.description ?? ''}
			rows={3}
		/>
		<Input
			name="tags"
			label={m.publish_tags()}
			value={service.tags.join(', ')}
			placeholder={m.publish_tags_hint()}
		/>

		<div class="grid grid-cols-1 gap-4 md:grid-cols-4">
			<Select
				name="service_type"
				label={m.publish_type()}
				options={serviceTypes}
				value={service.service_type}
				required
			/>
			<Input name="version" label={m.publish_version()} value={service.version} />
			<Select
				name="execution_mode"
				label={m.publish_execution()}
				options={executionModes}
				value={service.execution_mode}
				required
			/>
			<Select
				name="status"
				label={m.invocation_status()}
				options={statusOptions}
				value={service.status}
				required
			/>
		</div>

		<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
			<Select
				name="price_type"
				label={m.publish_pricing()}
				options={priceTypes}
				value={service.price_type}
				required
			/>
			<Input
				name="price_amount"
				label={m.publish_price_amount()}
				type="number"
				value={service.price_amount != null ? String(service.price_amount) : ''}
			/>
			<Input name="currency" label={m.publish_currency()} value={service.currency} />
		</div>

		<Select
			name="visibility"
			label={m.publish_visibility()}
			options={visibilityOptions}
			value={service.visibility}
			required
		/>

		<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<Textarea
				name="input_schema"
				label={m.publish_input_schema()}
				value={JSON.stringify(service.input_schema, null, 2)}
				rows={6}
			/>
			<Textarea
				name="output_schema"
				label={m.publish_output_schema()}
				value={JSON.stringify(service.output_schema, null, 2)}
				rows={6}
			/>
		</div>

		<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<Input
				name="max_concurrency"
				label={m.publish_max_concurrency()}
				type="number"
				value={service.max_concurrency != null ? String(service.max_concurrency) : ''}
			/>
			<Input
				name="timeout_s"
				label={m.publish_timeout()}
				type="number"
				value={service.timeout_s != null ? String(service.timeout_s) : ''}
			/>
		</div>

		<Textarea
			name="terms_of_use"
			label={m.publish_terms()}
			value={service.terms_of_use ?? ''}
			rows={3}
		/>

		<div class="flex gap-3">
			<Button type="submit">{m.edit_submit()}</Button>
			<Button variant="outline" href={localizeHref(`/services/${service.slug}`)}
				>{m.common_cancel()}</Button
			>
		</div>
	</form>
</Card>
