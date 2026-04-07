<script lang="ts">
	import * as m from '$lib/paraglide/messages';
	import { localizeHref } from '$lib/paraglide/runtime';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import StatusBadge from '$lib/components/marketplace/StatusBadge.svelte';
	import Spinner from '$lib/components/ui/Spinner.svelte';
	import type { Invocation } from '$lib/types/marketplace';
	import type { InvocationStatus } from '$lib/types/marketplace';

	let { data } = $props();

	const TERMINAL_STATUSES = new Set(['succeeded', 'failed', 'cancelled']);
	const inv = $derived(data.invocation as Invocation);

	let liveStatus = $state<InvocationStatus | null>(null);
	let liveResultPayload = $state<Record<string, unknown> | null | undefined>(undefined);
	let liveErrorMessage = $state<string | null | undefined>(undefined);
	let liveStartedAt = $state<string | null | undefined>(undefined);
	let liveEndedAt = $state<string | null | undefined>(undefined);
	let liveCostFinal = $state<number | null | undefined>(undefined);
	let liveArtifactUri = $state<string | null | undefined>(undefined);

	const status = $derived(liveStatus ?? inv.status);
	const resultPayload = $derived(liveResultPayload ?? inv.result_payload);
	const errorMessage = $derived(liveErrorMessage ?? inv.error_message);
	const startedAt = $derived(liveStartedAt ?? inv.started_at);
	const endedAt = $derived(liveEndedAt ?? inv.ended_at);
	const costFinal = $derived(liveCostFinal ?? inv.cost_final);
	const artifactUri = $derived(liveArtifactUri ?? inv.artifact_uri);
	const artifactHref = $derived.by(() => {
		if (!artifactUri) return null;
		return new URL(artifactUri, data.apiBaseUrl).toString();
	});
	const isLive = $derived(!TERMINAL_STATUSES.has(status));

	function applyInvocationUpdate(update: {
		status?: InvocationStatus;
		result_payload?: Record<string, unknown> | null;
		error_message?: string | null;
		started_at?: string | null;
		ended_at?: string | null;
		cost_final?: number | null;
		artifact_uri?: string | null;
	}): void {
		if (update.status) liveStatus = update.status;
		if (update.result_payload !== undefined) liveResultPayload = update.result_payload;
		if (update.error_message !== undefined) liveErrorMessage = update.error_message;
		if (update.started_at !== undefined) liveStartedAt = update.started_at;
		if (update.ended_at !== undefined) liveEndedAt = update.ended_at;
		if (update.cost_final !== undefined) liveCostFinal = update.cost_final;
		if (update.artifact_uri !== undefined) liveArtifactUri = update.artifact_uri;
	}

	$effect(() => {
		if (!isLive) return;

		const ws = new WebSocket(data.wsUrl);

		ws.onmessage = (event) => {
			const update = JSON.parse(event.data);
			if (update.error) {
				liveErrorMessage = update.error;
				return;
			}
			applyInvocationUpdate({
				status: update.status as InvocationStatus,
				result_payload: update.result_payload ?? undefined,
				error_message: update.error_message ?? undefined,
				started_at: update.started_at ?? undefined,
				ended_at: update.ended_at ?? undefined,
				cost_final: update.cost_final ?? undefined,
				artifact_uri: update.artifact_uri ?? undefined,
			});
		};

		ws.onerror = () => {
			liveErrorMessage = 'Live status connection failed';
		};

		return () => {
			if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
				ws.close();
			}
		};
	});

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
		<div class="flex items-center gap-2">
			<StatusBadge status={status} />
			{#if isLive}
				<Spinner size="sm" />
				<span class="text-muted-foreground text-xs">Live</span>
			{/if}
		</div>
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
		{#if resultPayload}
			<Card>
				<h3 class="text-foreground mb-2 text-sm font-semibold">{m.invocation_result()}</h3>
				<pre class="text-foreground bg-muted overflow-x-auto rounded-md p-3 text-sm">{formatJson(
						resultPayload
					)}</pre>
			</Card>
		{/if}

		<!-- Error -->
		{#if errorMessage}
			<Card>
				<h3 class="text-destructive mb-2 text-sm font-semibold">{m.invocation_error()}</h3>
				<p class="text-destructive text-sm">{errorMessage}</p>
			</Card>
		{/if}

		<!-- Artifact -->
		{#if artifactUri}
			<Card>
				<h3 class="text-foreground mb-2 text-sm font-semibold">{m.invocation_artifact()}</h3>
				<a href={artifactHref} class="text-accent text-sm break-all hover:underline"
					>{artifactHref}</a
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
					<dd><StatusBadge status={status} /></dd>
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
					<dd class="text-foreground font-medium">{formatCost(costFinal, inv.currency)}</dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.invocation_created()}</dt>
					<dd class="text-foreground font-medium">{formatDate(inv.created_at)}</dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.invocation_started()}</dt>
					<dd class="text-foreground font-medium">{formatDate(startedAt)}</dd>
				</div>
				<div>
					<dt class="text-muted-foreground">{m.invocation_ended()}</dt>
					<dd class="text-foreground font-medium">{formatDate(endedAt)}</dd>
				</div>
			</dl>
		</Card>
	</div>
</div>
