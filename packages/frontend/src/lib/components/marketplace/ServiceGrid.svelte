<script lang="ts">
    import type { ServiceSummary } from '$lib/types/marketplace';
    import ServiceCard from './ServiceCard.svelte';

    interface Props {
        services: ServiceSummary[];
    }

    let { services }: Props = $props();
</script>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {#each services as service (service.id)}
        <ServiceCard {service} />
    {/each}
</div>
