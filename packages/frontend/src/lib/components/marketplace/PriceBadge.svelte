<!--
@component
Affiche le prix d'un service en badge coloré, en choisissant le libellé selon
`priceType` (gratuit / fixe / au temps) et en se rabattant sur « non défini »
quand un montant est requis mais absent.
-->
<script lang="ts">
    import * as m from '$lib/paraglide/messages';
    import Badge from '$lib/components/ui/Badge.svelte';
    import type { PriceType } from '$lib/types/marketplace';

    interface Props {
        priceType: PriceType;
        priceAmount?: number | null;
        currency?: string;
    }

    let { priceType, priceAmount, currency = 'EUR' }: Props = $props();
</script>

{#if priceType === 'free'}
    <Badge variant="success">{m.price_free()}</Badge>
{:else if priceType === 'fixed' && priceAmount != null}
    <Badge variant="outline">{m.price_fixed({ amount: String(priceAmount), currency })}</Badge>
{:else if priceType === 'time' && priceAmount != null}
    <Badge variant="outline">{m.price_time({ amount: String(priceAmount), currency })}</Badge>
{:else}
    <Badge variant="secondary">{m.price_not_set()}</Badge>
{/if}
