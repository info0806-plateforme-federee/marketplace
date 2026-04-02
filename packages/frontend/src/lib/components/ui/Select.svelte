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
		value = $bindable(''),
		options,
		placeholder,
		required = false,
		disabled = false,
		class: className = '',
		onchange
	}: Props = $props();
</script>

<div>
	{#if label}
		<label for={name} class="text-foreground mb-1 block text-sm font-medium"
			>{label}{#if required}<span class="text-destructive ml-0.5">*</span>{/if}</label
		>
	{/if}
	<select
		{name}
		id={name}
		bind:value
		{required}
		{disabled}
		{onchange}
		class="border-input bg-surface text-foreground focus-visible:ring-ring flex h-10 w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none disabled:opacity-50 {className}"
	>
		{#if placeholder}
			<option value="" disabled selected={!value}>{placeholder}</option>
		{/if}
		{#each options as opt (opt.value)}
			<option value={opt.value} selected={opt.value === value}>{opt.label}</option>
		{/each}
	</select>
</div>
