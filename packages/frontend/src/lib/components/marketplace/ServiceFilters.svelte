<!--
@component
Barre de filtres pour le catalogue de services (recherche + sélecteurs
catégorie/type/prix). Les filtres actifs vivent dans la chaîne de requête de
l'URL : en modifier un navigue avec les params mis à jour (en réinitialisant la
page), donc le `load` du catalogue se relance côté serveur. Les valeurs courantes
sont dérivées de l'URL pour que les contrôles restent synchronisés à la navigation
avant/arrière.
-->
<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/state';
    import * as m from '$lib/paraglide/messages';
    import SearchInput from '$lib/components/ui/SearchInput.svelte';
    import Select from '$lib/components/ui/Select.svelte';
    import Button from '$lib/components/ui/Button.svelte';

    const categoryOptions = $derived([
        { value: '', label: m.common_all() },
        { value: 'ml', label: 'ML' },
        { value: 'data', label: m.type_data() },
        { value: 'compute', label: m.type_compute() },
        { value: 'utility', label: m.type_utility() },
    ]);

    const typeOptions = $derived([
        { value: '', label: m.common_all() },
        { value: 'compute', label: m.type_compute() },
        { value: 'data', label: m.type_data() },
        { value: 'model', label: m.type_model() },
        { value: 'utility', label: m.type_utility() },
    ]);

    const priceOptions = $derived([
        { value: '', label: m.common_all() },
        { value: 'free', label: m.price_free() },
        { value: 'fixed', label: 'Fixed' },
        { value: 'time', label: 'Time-based' },
    ]);

    /** Pose/efface un param de requête et navigue ; réinitialise la pagination à la page 1. */
    function updateFilter(key: string, value: string) {
        const params = new URLSearchParams(page.url.searchParams);
        if (value) {
            params.set(key, value);
        } else {
            params.delete(key);
        }
        params.delete('page');
        goto(`?${params.toString()}`, { replaceState: true, keepFocus: true });
    }

    /** Abandonne tous les filtres en naviguant vers le chemin nu. */
    function clearFilters() {
        goto(page.url.pathname, { replaceState: true });
    }

    let search = $derived(page.url.searchParams.get('search') ?? '');
    let category = $derived(page.url.searchParams.get('category') ?? '');
    let serviceType = $derived(page.url.searchParams.get('service_type') ?? '');
    let priceType = $derived(page.url.searchParams.get('price_type') ?? '');
    let hasFilters = $derived(!!(search || category || serviceType || priceType));
</script>

<div class="space-y-4">
    <SearchInput
        value={search}
        placeholder={m.common_search()}
        onsearch={(v) => updateFilter('search', v)}
    />
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Select
            name="category"
            label={m.catalog_filter_category()}
            value={category}
            options={categoryOptions}
            onchange={(e) => updateFilter('category', (e.target as HTMLSelectElement).value)}
        />
        <Select
            name="service_type"
            label={m.catalog_filter_type()}
            value={serviceType}
            options={typeOptions}
            onchange={(e) => updateFilter('service_type', (e.target as HTMLSelectElement).value)}
        />
        <Select
            name="price_type"
            label={m.catalog_filter_price()}
            value={priceType}
            options={priceOptions}
            onchange={(e) => updateFilter('price_type', (e.target as HTMLSelectElement).value)}
        />
    </div>
    {#if hasFilters}
        <Button variant="ghost" size="sm" onclick={clearFilters}>
            {m.common_clear_filters()}
        </Button>
    {/if}
</div>
