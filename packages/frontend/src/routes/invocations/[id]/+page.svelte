<!--
@component
Page de détail d'une invocation avec mises à jour en direct.

L'invocation initiale est chargée côté serveur dans `data`. Tant que l'invocation
n'est pas terminale, une WebSocket (`data.wsUrl`) diffuse des mises à jour de statut
stockées dans les variables d'état `live*` ; chaque champ affiché est un `$derived`
qui préfère la valeur en direct à celle chargée côté serveur (`live ?? inv`).
Séparément, dès qu'une URL de résultat est connue, le JSON de résultat est récupéré
(via proxy) pour affichage.
-->
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

	// Statuts après lesquels plus aucune mise à jour n'arrive (la WS peut être fermée).
	const TERMINAL_STATUSES = new Set(['succeeded', 'failed', 'cancelled']);
	const inv = $derived(data.invocation as Invocation);

	// Valeurs en direct poussées par la WebSocket ; `undefined`/`null` signifie « pas
	// encore de valeur en direct », donc les champs dérivés ci-dessous se rabattent
	// sur l'invocation chargée côté serveur.
	let liveStatus = $state<InvocationStatus | null>(null);
	let liveResultUrl = $state<string | null | undefined>(undefined);
	let liveArtifactUrl = $state<string | null | undefined>(undefined);
	let liveErrorMessage = $state<string | null | undefined>(undefined);
	let liveStartedAt = $state<string | null | undefined>(undefined);
	let liveEndedAt = $state<string | null | undefined>(undefined);
	let liveCostFinal = $state<number | null | undefined>(undefined);

	// Chaque champ préfère la valeur en direct, en se rabattant sur celle côté serveur.
	const status = $derived(liveStatus ?? inv.status);
	const resultUrl = $derived(liveResultUrl ?? inv.result_url);
	const artifactUrl = $derived(liveArtifactUrl ?? inv.artifact_url);
	const resultProxyUrl = $derived(`${data.apiBaseUrl}/api/invocations/${inv.id}/result-file`);
	const artifactProxyUrl = $derived(`${data.apiBaseUrl}/api/invocations/${inv.id}/artifact`);
	const artifactFilename = $derived(filenameFromUrl(artifactUrl) ?? `${inv.id}-artifact`);
	const errorMessage = $derived(liveErrorMessage ?? inv.error_message);
	const startedAt = $derived(liveStartedAt ?? inv.started_at);
	const endedAt = $derived(liveEndedAt ?? inv.ended_at);
	const costFinal = $derived(liveCostFinal ?? inv.cost_final);
	// Vrai tant que l'invocation peut encore changer (pilote la WS + le badge « Live »).
	const isLive = $derived(!TERMINAL_STATUSES.has(status));

	/** Extrait un nom de fichier de téléchargement d'un chemin d'URL, ou null si aucun n'est exploitable. */
	function filenameFromUrl(url: string | null): string | null {
		if (!url) return null;
		try {
			const pathname = new URL(url).pathname;
			const filename = decodeURIComponent(pathname.split('/').filter(Boolean).at(-1) ?? '');
			return filename && filename !== '.' && filename !== '..' ? filename : null;
		} catch {
			return null;
		}
	}

	// JSON de résultat récupéré (via le proxy de la marketplace) depuis le S3 du fournisseur.
	let resultData = $state<Record<string, unknown> | null>(null);
	let resultLoading = $state(false);
	let resultError = $state<string | null>(null);

	// Dès qu'une URL de résultat devient disponible, récupère et parse le JSON de résultat.
	$effect(() => {
		if (resultUrl) {
			resultLoading = true;
			resultError = null;
			fetch(resultProxyUrl)
				.then((r) => {
					if (!r.ok) throw new Error(`HTTP ${r.status}`);
					return r.json();
				})
				.then((data) => {
					resultData = data;
					resultLoading = false;
				})
				.catch((e) => {
					resultError = e.message;
					resultLoading = false;
				});
		} else {
			resultData = null;
		}
	});

	/** Copie une mise à jour de statut de la WS dans les variables d'état `live*` correspondantes. */
	function applyInvocationUpdate(update: {
		status?: InvocationStatus;
		result_url?: string | null;
		artifact_url?: string | null;
		error_message?: string | null;
		started_at?: string | null;
		ended_at?: string | null;
		cost_final?: number | null;
	}): void {
		if (update.status) liveStatus = update.status;
		if (update.result_url !== undefined) liveResultUrl = update.result_url;
		if (update.artifact_url !== undefined) liveArtifactUrl = update.artifact_url;
		if (update.error_message !== undefined) liveErrorMessage = update.error_message;
		if (update.started_at !== undefined) liveStartedAt = update.started_at;
		if (update.ended_at !== undefined) liveEndedAt = update.ended_at;
		if (update.cost_final !== undefined) liveCostFinal = update.cost_final;
	}

	// Ouvre une WebSocket tant que l'invocation est en direct ; la ferme au démontage
	// ou dès qu'elle atteint un statut terminal (l'effet se relance quand `isLive` passe à false).
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
				result_url: update.result_url ?? undefined,
				artifact_url: update.artifact_url ?? undefined,
				error_message: update.error_message ?? undefined,
				started_at: update.started_at ?? undefined,
				ended_at: update.ended_at ?? undefined,
				cost_final: update.cost_final ?? undefined,
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

	/** Formate un horodatage ISO en date-heure localisée complète, ou un tiret cadratin si null. */
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

	/** Formate un montant de coût avec devise, ou un tiret cadratin si inconnu. */
	function formatCost(amount: number | null, currency: string): string {
		if (amount == null) return '—';
		return `${amount} ${currency}`;
	}

	/** Affiche un objet en JSON indenté, ou un tiret cadratin si vide/null. */
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
	<!-- Principal -->
	<div class="space-y-6 lg:col-span-2">
		<!-- Entrée -->
		<Card>
			<h3 class="text-foreground mb-2 text-sm font-semibold">{m.invocation_input()}</h3>
			<pre class="text-foreground bg-muted overflow-x-auto rounded-md p-3 text-sm">{formatJson(
					inv.input_payload
				)}</pre>
		</Card>

		<!-- Résultat -->
		{#if resultLoading}
			<Card>
				<h3 class="text-foreground mb-2 text-sm font-semibold">{m.invocation_result()}</h3>
				<div class="flex items-center gap-2 text-sm text-muted-foreground">
					<Spinner size="sm" />
					<span>Loading result...</span>
				</div>
			</Card>
		{:else if resultData}
			<Card>
				<h3 class="text-foreground mb-2 text-sm font-semibold">{m.invocation_result()}</h3>
				<pre class="text-foreground bg-muted overflow-x-auto rounded-md p-3 text-sm">{formatJson(
						resultData
					)}</pre>
			</Card>
		{:else if resultError}
			<Card>
				<h3 class="text-foreground mb-2 text-sm font-semibold">{m.invocation_result()}</h3>
				<p class="text-destructive text-sm">Failed to load result: {resultError}</p>
			</Card>
		{/if}

		<!-- Erreur -->
		{#if errorMessage}
			<Card>
				<h3 class="text-destructive mb-2 text-sm font-semibold">{m.invocation_error()}</h3>
				<p class="text-destructive text-sm">{errorMessage}</p>
			</Card>
		{/if}

		<!-- Artefact -->
		{#if artifactUrl}
			<Card>
				<h3 class="text-foreground mb-2 text-sm font-semibold">{m.invocation_artifact()}</h3>
				<a
					href={artifactProxyUrl}
					class="text-accent text-sm break-all hover:underline"
					download={artifactFilename}
				>
					{artifactFilename}
				</a>
			</Card>
		{/if}
	</div>

	<!-- Barre latérale -->
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
