<script lang="ts">
    interface Props {
        page: number;
        totalPages: number;
        onPageChange: (page: number) => void;
    }

    let { page, totalPages, onPageChange }: Props = $props();
</script>

{#if totalPages > 1}
    <nav class="flex items-center justify-center gap-2 mt-6" aria-label="Pagination">
        <button
            onclick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            aria-label="Previous page"
            class="inline-flex items-center justify-center h-9 px-3 rounded-md border border-border text-sm text-foreground hover:bg-accent/10 disabled:opacity-50 disabled:pointer-events-none"
        >
            &larr;
        </button>

        {#each Array.from({ length: totalPages }, (_, i) => i + 1) as p}
            {#if p === 1 || p === totalPages || (p >= page - 1 && p <= page + 1)}
                <button
                    onclick={() => onPageChange(p)}
                    aria-label="Page {p}"
                    aria-current={p === page ? 'page' : undefined}
                    class="inline-flex items-center justify-center h-9 w-9 rounded-md text-sm {p === page
                        ? 'bg-primary text-primary-foreground'
                        : 'border border-border text-foreground hover:bg-accent/10'}"
                >
                    {p}
                </button>
            {:else if p === page - 2 || p === page + 2}
                <span class="text-muted-foreground" aria-hidden="true">...</span>
            {/if}
        {/each}

        <button
            onclick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            aria-label="Next page"
            class="inline-flex items-center justify-center h-9 px-3 rounded-md border border-border text-sm text-foreground hover:bg-accent/10 disabled:opacity-50 disabled:pointer-events-none"
        >
            &rarr;
        </button>
    </nav>
{/if}
