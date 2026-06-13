<!--
@component
Curseur de plage avec affichage en direct de la valeur (et `unit` optionnelle).
`value` est `bind:`-able ; un input caché le reflète pour que la valeur soit
envoyée avec le formulaire.
-->
<script lang="ts">
	interface Props {
		name: string;
		label?: string;
		min?: number;
		max?: number;
		step?: number;
		value?: number;
		unit?: string;
	}

	let {
		name,
		label,
		min = 0,
		max = 100,
		step = 1,
		value = $bindable(0),
		unit = ''
	}: Props = $props();
</script>

<div>
	{#if label}
		<label for={name} class="text-foreground mb-1 block text-sm font-medium">{label}</label>
	{/if}
	<div class="flex items-center gap-3">
		<input
			id={name}
			type="range"
			{min}
			{max}
			{step}
			bind:value
			class="bg-secondary accent-primary h-2 flex-1 cursor-pointer appearance-none rounded-lg"
		/>
		<span class="text-foreground min-w-[4rem] text-right text-sm font-medium">
			{value}{unit ? ` ${unit}` : ''}
		</span>
	</div>
	<input type="hidden" {name} value={String(value)} />
</div>
