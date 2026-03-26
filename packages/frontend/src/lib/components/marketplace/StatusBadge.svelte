<script lang="ts">
    import * as m from '$lib/paraglide/messages';
    import Badge from '$lib/components/ui/Badge.svelte';

    interface Props {
        status: string;
    }

    let { status }: Props = $props();

    const config: Record<
        string,
        { variant: 'success' | 'warning' | 'destructive' | 'secondary' | 'default'; label: () => string }
    > = {
        active: { variant: 'success', label: () => m.status_active() },
        disabled: { variant: 'secondary', label: () => m.status_disabled() },
        draft: { variant: 'warning', label: () => m.status_draft() },
        deprecated: { variant: 'secondary', label: () => m.status_deprecated() },
        pending: { variant: 'warning', label: () => m.status_pending() },
        accepted: { variant: 'default', label: () => m.status_accepted() },
        running: { variant: 'warning', label: () => m.status_running() },
        succeeded: { variant: 'success', label: () => m.status_succeeded() },
        failed: { variant: 'destructive', label: () => m.status_failed() },
        cancelled: { variant: 'secondary', label: () => m.status_cancelled() },
    };

    let entry = $derived(config[status] ?? { variant: 'secondary' as const, label: () => status });
</script>

<Badge variant={entry.variant}>{entry.label()}</Badge>
