<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import * as m from '$lib/paraglide/messages';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import ServiceFilters from '$lib/components/marketplace/ServiceFilters.svelte';
	import ServiceGrid from '$lib/components/marketplace/ServiceGrid.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Pagination from '$lib/components/ui/Pagination.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import { localizeHref } from '$lib/paraglide/runtime';

	let { data } = $props();

	function handlePageChange(newPage: number) {
		const params = new URLSearchParams(page.url.searchParams);
		params.set('page', String(newPage));
		goto(`?${params.toString()}`, { replaceState: true });
	}
</script>

<svelte:head>
	<title>{m.catalog_title()}</title>
</svelte:head>

<PageHeader title={m.catalog_title()} subtitle={m.catalog_subtitle()} />

<div class="mb-6">
	<ServiceFilters />
</div>

{#if data.services.items.length === 0}
	<EmptyState message={m.common_no_results()}>
		{#snippet children()}
			<Button variant="outline" href={localizeHref('/services/publish')}>
				{m.home_publish_service()}
			</Button>
		{/snippet}
	</EmptyState>
{:else}
	<ServiceGrid services={data.services.items} />
	<Pagination
		page={data.services.page}
		totalPages={data.services.total_pages}
		onPageChange={handlePageChange}
	/>
{/if}
