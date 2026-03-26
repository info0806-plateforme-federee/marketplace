<script lang="ts">
    interface Props {
        label?: string;
        name: string;
        value?: string;
        placeholder?: string;
        rows?: number;
        required?: boolean;
        disabled?: boolean;
        error?: string;
        class?: string;
        oninput?: (e: Event) => void;
    }

    let {
        label,
        name,
        value = '',
        placeholder,
        rows = 4,
        required = false,
        disabled = false,
        error,
        class: className = '',
        oninput,
    }: Props = $props();
</script>

<div>
    {#if label}
        <label for={name} class="block text-sm font-medium text-foreground mb-1">{label}</label>
    {/if}
    <textarea
        {name}
        id={name}
        {value}
        {placeholder}
        {rows}
        {required}
        {disabled}
        {oninput}
        class="flex w-full rounded-md border border-input bg-surface px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 {error
            ? 'border-destructive'
            : ''} {className}"
    ></textarea>
    {#if error}
        <p class="mt-1 text-sm text-destructive">{error}</p>
    {/if}
</div>
