<!--
@component
Zone de texte multiligne avec libellé et `error` inline optionnelle. `value` est
`bind:`-able et `rows` fixe la hauteur visible.
-->
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
		value = $bindable(''),
		placeholder,
		rows = 4,
		required = false,
		disabled = false,
		error,
		class: className = '',
		oninput
	}: Props = $props();
</script>

<div>
	{#if label}
		<label for={name} class="text-foreground mb-1 block text-sm font-medium"
			>{label}{#if required}<span class="text-destructive ml-0.5">*</span>{/if}</label
		>
	{/if}
	<textarea
		{name}
		id={name}
		bind:value
		{placeholder}
		{rows}
		{required}
		{disabled}
		{oninput}
		class="border-input bg-surface text-foreground placeholder:text-muted-foreground focus-visible:ring-ring flex w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none disabled:opacity-50 {error
			? 'border-destructive'
			: ''} {className}"
	></textarea>
	{#if error}
		<p class="text-destructive mt-1 text-sm">{error}</p>
	{/if}
</div>
