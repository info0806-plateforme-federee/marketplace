<script lang="ts">
    import type { Snippet } from 'svelte';

    interface Props {
        message: string;
        children?: Snippet;
    }

    let { message, children }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center py-12 text-center">
    <svg
        class="h-12 w-12 text-muted-foreground/50 mb-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="1.5"
        aria-hidden="true"
    >
        <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
        />
    </svg>
    <p class="text-muted-foreground text-sm">{message}</p>
    {#if children}
        <div class="mt-4">
            {@render children()}
        </div>
    {/if}
</div>
