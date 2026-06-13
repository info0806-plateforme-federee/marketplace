<!--
@component
Tuile de catalogue pour un service : nom, badge de prix, description tronquée,
badges de catégorie et de type, et nom du fournisseur. Toute la carte est un lien
vers la page de détail du service. `m.*` sont des fonctions de message localisé
(paraglide).
-->
<script lang="ts">
    import type { ServiceSummary } from '$lib/types/marketplace';
    import { localizeHref } from '$lib/paraglide/runtime';
    import * as m from '$lib/paraglide/messages';
    import Card from '$lib/components/ui/Card.svelte';
    import Badge from '$lib/components/ui/Badge.svelte';
    import PriceBadge from './PriceBadge.svelte';

    interface Props {
        service: ServiceSummary;
    }

    let { service }: Props = $props();

    const typeLabels: Record<string, () => string> = {
        compute: () => m.type_compute(),
        data: () => m.type_data(),
        model: () => m.type_model(),
        utility: () => m.type_utility(),
    };
</script>

<a href={localizeHref(`/services/${service.slug}`)} class="block group">
    <Card class="h-full transition-shadow hover:shadow-md">
        <div class="flex items-start justify-between gap-2 mb-3">
            <h3 class="font-semibold text-foreground group-hover:text-accent transition-colors line-clamp-1">
                {service.name}
            </h3>
            <PriceBadge priceType={service.price_type} priceAmount={service.price_amount} currency={service.currency} />
        </div>

        {#if service.description}
            <p class="text-sm text-muted-foreground line-clamp-2 mb-3">{service.description}</p>
        {/if}

        <div class="flex items-center gap-2 flex-wrap mt-auto">
            <Badge variant="secondary">{service.category}</Badge>
            {#if typeLabels[service.service_type]}
                <Badge variant="outline">{typeLabels[service.service_type]()}</Badge>
            {/if}
        </div>

        {#if service.provider_site}
            <p class="text-xs text-muted-foreground mt-3">
                {m.service_by({ provider: service.provider_site.name })}
            </p>
        {/if}
    </Card>
</a>
