<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import * as m from '$lib/paraglide/messages';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import InvocationRow from '$lib/components/marketplace/InvocationRow.svelte';
	import Select from '$lib/components/ui/Select.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import Pagination from '$lib/components/ui/Pagination.svelte';

	let { data } = $props();

	const statusOptions = [
		{ value: '', label: m.common_all() },
		{ value: 'pending', label: m.status_pending() },
		{ value: 'accepted', label: m.status_accepted() },
		{ value: 'running', label: m.status_running() },
		{ value: 'succeeded', label: m.status_succeeded() },
		{ value: 'failed', label: m.status_failed() },
		{ value: 'cancelled', label: m.status_cancelled() }
	];

	function updateStatus(e: Event) {
		const value = (e.target as HTMLSelectElement).value;
		const params = new URLSearchParams(page.url.searchParams);
		if (value) params.set('status', value);
		else params.delete('status');
		params.delete('page');
		goto(`?${params.toString()}`, { replaceState: true });
	}

	function handlePageChange(newPage: number) {
		const params = new URLSearchParams(page.url.searchParams);
		params.set('page', String(newPage));
		goto(`?${params.toString()}`, { replaceState: true });
	}
</script>

<svelte:head>
	<title>{m.invocations_title()}</title>
</svelte:head>

<PageHeader title={m.invocations_title()} subtitle={m.invocations_subtitle()} />

<div class="mb-6 max-w-xs">
	<Select
		name="status_filter"
		label={m.invocation_status()}
		value={page.url.searchParams.get('status') ?? ''}
		options={statusOptions}
		onchange={updateStatus}
	/>
</div>

{#if data.invocations.items.length === 0}
	<EmptyState message={m.invocations_empty()} />
{:else}
	<div class="space-y-2">
		{#each data.invocations.items as invocation (invocation.id)}
			<InvocationRow {invocation} />
		{/each}
	</div>
	<Pagination
		page={data.invocations.page}
		totalPages={data.invocations.total_pages}
		onPageChange={handlePageChange}
	/>
{/if}
