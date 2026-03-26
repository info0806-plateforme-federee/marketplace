<script lang="ts">
    interface Props {
        label?: string;
        name: string;
        type?: string;
        value?: string;
        placeholder?: string;
        required?: boolean;
        disabled?: boolean;
        error?: string;
        class?: string;
        oninput?: (e: Event) => void;
    }

    let {
        label,
        name,
        type = 'text',
        value = '',
        placeholder,
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
    <input
        {name}
        id={name}
        {type}
        {value}
        {placeholder}
        {required}
        {disabled}
        {oninput}
        class="flex h-10 w-full rounded-md border border-input bg-surface px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 {error
            ? 'border-destructive'
            : ''} {className}"
    />
    {#if error}
        <p class="mt-1 text-sm text-destructive">{error}</p>
    {/if}
</div>
