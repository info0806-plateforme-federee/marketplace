<!--
@component
Page d'accueil : statistiques de tête, boutons d'action rapide, et une grille de
services mis en avant. `data` provient du loader `+page.server.ts` de cette route.
-->
<script lang="ts">
	import * as m from '$lib/paraglide/messages';
	import { localizeHref } from '$lib/paraglide/runtime';
	import Button from '$lib/components/ui/Button.svelte';
	import StatsCard from '$lib/components/marketplace/StatsCard.svelte';
	import ServiceGrid from '$lib/components/marketplace/ServiceGrid.svelte';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';

	let { data } = $props();
</script>

<svelte:head>
	<title>{m.home_title()}</title>
</svelte:head>

<PageHeader title={m.home_title()} subtitle={m.home_subtitle()} />

<!-- Statistiques -->
<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
	<StatsCard label={m.home_stats_services()} value={data.stats.totalServices} />
	<StatsCard label={m.home_stats_invocations()} value={data.stats.totalInvocations} />
	<StatsCard label={m.home_stats_sites()} value={data.stats.activeSites} />
	<StatsCard label={m.home_stats_categories()} value={data.stats.categories} />
</div>

<!-- Actions rapides -->
<div class="flex gap-3 mb-8">
	<Button href={localizeHref('/services')}>{m.home_browse_catalog()}</Button>
	<Button variant="outline" href={localizeHref('/services/publish')}>{m.home_publish_service()}</Button>
</div>

<!-- Services mis en avant -->
{#if data.featuredServices.length > 0}
	<h2 class="text-lg font-semibold text-foreground mb-4">{m.home_featured()}</h2>
	<ServiceGrid services={data.featuredServices} />
{/if}
