<!--
@component
Une ligne de la liste des invocations : service, date de création, badge de statut
et coût. Lien vers la page de détail de l'invocation. Affiche le coût estimé s'il
est présent, sinon le coût final (ou un tiret cadratin si ni l'un ni l'autre).
-->
<script lang="ts">
    import type { Invocation } from '$lib/types/marketplace';
    import { localizeHref } from '$lib/paraglide/runtime';
    import StatusBadge from './StatusBadge.svelte';

    interface Props {
        invocation: Invocation;
    }

    let { invocation }: Props = $props();

    /** Formate un horodatage ISO en date-heure localisée courte. */
    function formatDate(iso: string): string {
        return new Date(iso).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    }

    /** Formate un montant de coût avec sa devise, ou un tiret cadratin si inconnu. */
    function formatCost(amount: number | null, currency: string): string {
        if (amount == null) return '—';
        return `${amount} ${currency}`;
    }
</script>

<a
    href={localizeHref(`/invocations/${invocation.id}`)}
    class="flex items-center gap-4 px-4 py-3 rounded-lg border border-border bg-card hover:bg-muted/30 transition-colors"
>
    <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-foreground truncate">{invocation.service_id}</p>
        <p class="text-xs text-muted-foreground">{formatDate(invocation.created_at)}</p>
    </div>
    <StatusBadge status={invocation.status} />
    <div class="text-sm text-foreground w-24 text-right">
        {formatCost(invocation.cost_estimated ?? invocation.cost_final, invocation.currency)}
    </div>
</a>
