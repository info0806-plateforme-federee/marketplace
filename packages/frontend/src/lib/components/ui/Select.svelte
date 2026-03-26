<script lang="ts">
    interface Option {
        value: string;
        label: string;
    }

    interface Props {
        label?: string;
        name: string;
        value?: string;
        options: Option[];
        placeholder?: string;
        required?: boolean;
        disabled?: boolean;
        class?: string;
        onchange?: (e: Event) => void;
    }

    let {
        label,
        name,
        value = '',
        options,
        placeholder,
        required = false,
        disabled = false,
        class: className = '',
        onchange,
    }: Props = $props();
</script>

<div>
    {#if label}
        <label for={name} class="block text-sm font-medium text-foreground mb-1">{label}</label>
    {/if}
    <select
        {name}
        id={name}
        {value}
        {required}
        {disabled}
        {onchange}
        class="flex h-10 w-full rounded-md border border-input bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 {className}"
    >
        {#if placeholder}
            <option value="" disabled selected={!value}>{placeholder}</option>
        {/if}
        {#each options as opt}
            <option value={opt.value} selected={opt.value === value}>{opt.label}</option>
        {/each}
    </select>
</div>
