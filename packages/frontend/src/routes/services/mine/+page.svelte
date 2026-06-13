<!--
@component
Page de gestion « Mes services » : liste les services de ce site (tout
statut/visibilité) avec des actions Voir/Éditer, ou un état vide invitant
l'utilisateur à en publier un.
-->
<script lang="ts">
	import * as m from '$lib/paraglide/messages';
	import { localizeHref } from '$lib/paraglide/runtime';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import StatusBadge from '$lib/components/marketplace/StatusBadge.svelte';
	import PriceBadge from '$lib/components/marketplace/PriceBadge.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';

	let { data } = $props();
</script>

<svelte:head>
	<title>{m.my_services_title()}</title>
</svelte:head>

<PageHeader title={m.my_services_title()} subtitle={m.my_services_subtitle()}>
	{#snippet actions()}
		<Button href={localizeHref('/services/publish')}>{m.home_publish_service()}</Button>
	{/snippet}
</PageHeader>

{#if data.services.items.length === 0}
	<EmptyState message={m.my_services_empty()}>
		{#snippet children()}
			<Button href={localizeHref('/services/publish')}>{m.home_publish_service()}</Button>
		{/snippet}
	</EmptyState>
{:else}
	<div class="space-y-3">
		{#each data.services.items as service (service.id)}
			<Card class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
				<div class="min-w-0 flex-1">
					<div class="mb-1 flex items-center gap-2">
						<h3 class="text-foreground truncate font-medium">{service.name}</h3>
						<StatusBadge status={service.status} />
						<PriceBadge
							priceType={service.price_type}
							priceAmount={service.price_amount}
							currency={service.currency}
						/>
					</div>
					{#if service.description}
						<p class="text-muted-foreground line-clamp-1 text-sm">{service.description}</p>
					{/if}
				</div>
				<div class="flex items-center gap-2">
					<Button variant="outline" size="sm" href={localizeHref(`/services/${service.slug}`)}>
						{m.common_view()}
					</Button>
					<Button
						variant="ghost"
						size="sm"
						href={localizeHref(`/services/mine/${service.slug}/edit`)}
					>
						{m.common_edit()}
					</Button>
				</div>
			</Card>
		{/each}
	</div>
{/if}
