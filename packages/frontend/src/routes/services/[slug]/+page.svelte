<script lang="ts">
	import * as m from '$lib/paraglide/messages';
	import { localizeHref } from '$lib/paraglide/runtime';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import StatusBadge from '$lib/components/marketplace/StatusBadge.svelte';
	import PriceBadge from '$lib/components/marketplace/PriceBadge.svelte';
	import SchemaViewer from '$lib/components/marketplace/SchemaViewer.svelte';

	let { data } = $props();
	let service = $derived(data.service);

	const modeLabels: Record<string, () => string> = {
		sync: () => m.mode_sync(),
		async: () => m.mode_async(),
	};

	const visibilityLabels: Record<string, () => string> = {
		public: () => m.visibility_public(),
		private: () => m.visibility_private(),
		restricted: () => m.visibility_restricted(),
	};

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString(undefined, {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
		});
	}
</script>

<svelte:head>
	<title>{service.name}</title>
</svelte:head>

<PageHeader title={service.name} subtitle={service.description ?? ''}>
	{#snippet actions()}
		<Button href={localizeHref(`/services/${service.slug}/invoke`)}>
			{m.service_invoke()}
		</Button>
		<Button variant="outline" href={localizeHref('/services')}>
			{m.common_back()}
		</Button>
	{/snippet}
</PageHeader>

<!-- Meta info -->
<div class="flex flex-wrap items-center gap-2 mb-6">
	<StatusBadge status={service.status} />
	<Badge variant="secondary">{service.category}</Badge>
	<Badge variant="outline">{m.service_version({ version: service.version })}</Badge>
	<PriceBadge
		priceType={service.price_type}
		priceAmount={service.price_amount}
		currency={service.currency}
	/>
	{#if service.provider_site}
		<span class="text-sm text-muted-foreground">
			{m.service_by({ provider: service.provider_site.name })}
		</span>
	{/if}
</div>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
	<!-- Main content -->
	<div class="lg:col-span-2 space-y-6">
		<!-- Description -->
		{#if service.description}
			<Card>
				<p class="text-foreground whitespace-pre-wrap">{service.description}</p>
			</Card>
		{/if}

		<!-- Input Schema -->
		<Card>
			<SchemaViewer schema={service.input_schema} title={m.service_input_schema()} />
		</Card>

		<!-- Output Schema -->
		<Card>
			<SchemaViewer schema={service.output_schema} title={m.service_output_schema()} />
		</Card>

		<!-- Terms -->
		{#if service.terms_of_use}
			<Card>
				<h3 class="text-sm font-semibold text-foreground mb-2">{m.service_terms()}</h3>
				<p class="text-sm text-muted-foreground whitespace-pre-wrap">{service.terms_of_use}</p>
			</Card>
		{/if}
	</div>

	<!-- Sidebar -->
	<div class="space-y-6">
		<Card>
			<h3 class="text-sm font-semibold text-foreground mb-3">{m.service_details()}</h3>
			<dl class="space-y-3 text-sm">
				<div>
					<dt class="text-muted-foreground">{m.service_execution_mode()}</dt>
					<dd class="font-medium text-foreground">
						{modeLabels[service.execution_mode]?.() ?? service.execution_mode}
					</dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.service_visibility()}</dt>
					<dd class="font-medium text-foreground">
						{visibilityLabels[service.visibility]?.() ?? service.visibility}
					</dd>
				</div>
				{#if service.max_concurrency != null}
					<div>
						<dt class="text-muted-foreground">{m.service_max_concurrency()}</dt>
						<dd class="font-medium text-foreground">{service.max_concurrency}</dd>
					</div>
				{/if}
				{#if service.timeout_s != null}
					<div>
						<dt class="text-muted-foreground">{m.service_timeout()}</dt>
						<dd class="font-medium text-foreground">{service.timeout_s}s</dd>
					</div>
				{/if}
				<div>
					<dt class="text-muted-foreground">{m.service_created()}</dt>
					<dd class="font-medium text-foreground">{formatDate(service.created_at)}</dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.service_updated()}</dt>
					<dd class="font-medium text-foreground">{formatDate(service.updated_at)}</dd>
				</div>
			</dl>
		</Card>

		<!-- Tags -->
		{#if service.tags.length > 0}
			<Card>
				<h3 class="text-sm font-semibold text-foreground mb-2">Tags</h3>
				<div class="flex flex-wrap gap-1">
					{#each service.tags as tag}
						<Badge variant="outline">{tag}</Badge>
					{/each}
				</div>
			</Card>
		{/if}
	</div>
</div>
