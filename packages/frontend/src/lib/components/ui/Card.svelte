<script lang="ts">
    import type { Snippet } from 'svelte';

    interface Props {
        class?: string;
        children: Snippet;
        header?: Snippet;
        footer?: Snippet;
    }

    let { class: className = '', children, header, footer }: Props = $props();
</script>

<div class="rounded-lg border border-border bg-card text-card-foreground shadow-sm {className}">
    {#if header}
        <div class="p-6 pb-0">
            {@render header()}
        </div>
    {/if}
    <div class="p-6">
        {@render children()}
    </div>
    {#if footer}
        <div class="border-t border-border p-6 pt-4">
            {@render footer()}
        </div>
    {/if}
</div>
