<script lang="ts">
	import * as m from '$lib/paraglide/messages';
	import { localizeHref } from '$lib/paraglide/runtime';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import StatusBadge from '$lib/components/marketplace/StatusBadge.svelte';

	let { data } = $props();
	let inv = $derived(data.invocation);

	function formatDate(iso: string | null): string {
		if (!iso) return '—';
		return new Date(iso).toLocaleString(undefined, {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit'
		});
	}

	function formatCost(amount: number | null, currency: string): string {
		if (amount == null) return '—';
		return `${amount} ${currency}`;
	}

	function formatJson(obj: Record<string, unknown> | null): string {
		if (!obj || Object.keys(obj).length === 0) return '—';
		return JSON.stringify(obj, null, 2);
	}
</script>

<svelte:head>
	<title>Invocation {inv.id.slice(0, 8)}</title>
</svelte:head>

<PageHeader title="Invocation {inv.id.slice(0, 8)}...">
	{#snippet actions()}
		<StatusBadge status={inv.status} />
		<Button variant="outline" href={localizeHref('/invocations')}>{m.common_back()}</Button>
	{/snippet}
</PageHeader>

<div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
	<!-- Main -->
	<div class="space-y-6 lg:col-span-2">
		<!-- Input -->
		<Card>
			<h3 class="text-foreground mb-2 text-sm font-semibold">{m.invocation_input()}</h3>
			<pre class="text-foreground bg-muted overflow-x-auto rounded-md p-3 text-sm">{formatJson(
					inv.input_payload
				)}</pre>
		</Card>

		<!-- Result -->
		{#if inv.result_payload}
			<Card>
				<h3 class="text-foreground mb-2 text-sm font-semibold">{m.invocation_result()}</h3>
				<pre class="text-foreground bg-muted overflow-x-auto rounded-md p-3 text-sm">{formatJson(
						inv.result_payload
					)}</pre>
			</Card>
		{/if}

		<!-- Error -->
		{#if inv.error_message}
			<Card>
				<h3 class="text-destructive mb-2 text-sm font-semibold">{m.invocation_error()}</h3>
				<p class="text-destructive text-sm">{inv.error_message}</p>
			</Card>
		{/if}

		<!-- Artifact -->
		{#if inv.artifact_uri}
			<Card>
				<h3 class="text-foreground mb-2 text-sm font-semibold">{m.invocation_artifact()}</h3>
				<a href={inv.artifact_uri} class="text-accent text-sm break-all hover:underline"
					>{inv.artifact_uri}</a
				>
			</Card>
		{/if}
	</div>

	<!-- Sidebar -->
	<div class="space-y-6">
		<Card>
			<dl class="space-y-3 text-sm">
				<div>
					<dt class="text-muted-foreground">{m.invocation_status()}</dt>
					<dd><StatusBadge status={inv.status} /></dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.invocation_service()}</dt>
					<dd class="text-foreground font-medium">{inv.service_id}</dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.invocation_estimated_cost()}</dt>
					<dd class="text-foreground font-medium">
						{formatCost(inv.cost_estimated, inv.currency)}
					</dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.invocation_final_cost()}</dt>
					<dd class="text-foreground font-medium">{formatCost(inv.cost_final, inv.currency)}</dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.invocation_created()}</dt>
					<dd class="text-foreground font-medium">{formatDate(inv.created_at)}</dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.invocation_started()}</dt>
					<dd class="text-foreground font-medium">{formatDate(inv.started_at)}</dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.invocation_ended()}</dt>
					<dd class="text-foreground font-medium">{formatDate(inv.ended_at)}</dd>
				</div>
			</dl>
		</Card>
	</div>
</div>
