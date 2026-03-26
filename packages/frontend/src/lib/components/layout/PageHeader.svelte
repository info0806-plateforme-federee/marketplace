<script lang="ts">
    import type { Snippet } from 'svelte';

    interface Props {
        title: string;
        subtitle?: string;
        actions?: Snippet;
    }

    let { title, subtitle, actions }: Props = $props();
</script>

<div class="mb-8 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
    <div>
        <h1 class="text-2xl font-bold font-(family-name:--font-title) text-foreground">{title}</h1>
        {#if subtitle}
            <p class="mt-1 text-sm text-muted-foreground">{subtitle}</p>
        {/if}
    </div>
    {#if actions}
        <div class="flex items-center gap-2">
            {@render actions()}
        </div>
    {/if}
</div>
