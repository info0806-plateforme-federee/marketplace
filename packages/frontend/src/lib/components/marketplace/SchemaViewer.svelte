<script lang="ts">
    interface Props {
        schema: Record<string, unknown>;
        title?: string;
    }

    let { schema, title }: Props = $props();

    let entries = $derived(Object.entries(schema));
</script>

{#if title}
    <h3 class="text-sm font-semibold text-foreground mb-2">{title}</h3>
{/if}

{#if entries.length === 0}
    <p class="text-sm text-muted-foreground italic">No schema defined</p>
{:else}
    <div class="rounded-md border border-border overflow-hidden">
        <table class="w-full text-sm">
            <thead>
                <tr class="bg-muted">
                    <th class="text-left px-3 py-2 font-medium text-muted-foreground">Field</th>
                    <th class="text-left px-3 py-2 font-medium text-muted-foreground">Type</th>
                </tr>
            </thead>
            <tbody>
                {#each entries as [key, val], i}
                    <tr class="{i % 2 === 0 ? 'bg-card' : 'bg-muted/30'}">
                        <td class="px-3 py-2 font-mono text-foreground">{key}</td>
                        <td class="px-3 py-2 text-muted-foreground">{typeof val === 'string' ? val : JSON.stringify(val)}</td>
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
{/if}
