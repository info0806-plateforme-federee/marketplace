<script lang="ts">
	import Badge from './Badge.svelte';

	interface Props {
		name: string;
		label?: string;
		value?: string;
		placeholder?: string;
		suggestions?: string[];
	}

	let { name, label, value = $bindable(''), placeholder, suggestions = [] }: Props = $props();

	let tags: string[] = $state(
		value
			? value
					.split(',')
					.map((t) => t.trim())
					.filter(Boolean)
			: []
	);
	let inputValue = $state('');

	function syncValue() {
		value = tags.join(', ');
	}

	function addTag(tag: string) {
		const trimmed = tag.trim().toLowerCase();
		if (trimmed && !tags.includes(trimmed)) {
			tags = [...tags, trimmed];
			syncValue();
		}
		inputValue = '';
	}

	function removeTag(tag: string) {
		tags = tags.filter((t) => t !== tag);
		syncValue();
	}

	function handleKeydown(e: KeyboardEvent) {
		if ((e.key === 'Enter' || e.key === ',') && inputValue.trim()) {
			e.preventDefault();
			addTag(inputValue);
		}
		if (e.key === 'Backspace' && !inputValue && tags.length > 0) {
			tags = tags.slice(0, -1);
		}
	}

	let unusedSuggestions = $derived(suggestions.filter((s) => !tags.includes(s)));
</script>

<div>
	{#if label}
		<label for="{name}-input" class="text-foreground mb-1 block text-sm font-medium">{label}</label>
	{/if}

	<div
		class="border-input bg-surface focus-within:ring-ring flex min-h-10 flex-wrap items-center gap-1.5 rounded-md border px-3 py-2 focus-within:ring-2"
	>
		{#each tags as tag (tag)}
			<Badge variant="secondary">
				{tag}
				<button
					type="button"
					class="hover:text-destructive ml-1 inline-flex items-center"
					onclick={() => removeTag(tag)}
				>
					&times;
				</button>
			</Badge>
		{/each}
		<input
			id="{name}-input"
			type="text"
			bind:value={inputValue}
			onkeydown={handleKeydown}
			{placeholder}
			class="text-foreground placeholder:text-muted-foreground min-w-[120px] flex-1 border-none bg-transparent text-sm outline-none"
		/>
	</div>

	{#if unusedSuggestions.length > 0}
		<div class="mt-2 flex flex-wrap gap-1">
			{#each unusedSuggestions as suggestion (suggestion)}
				<button type="button" onclick={() => addTag(suggestion)}>
					<Badge variant="outline">{suggestion}</Badge>
				</button>
			{/each}
		</div>
	{/if}

	<input type="hidden" {name} value={tags.join(', ')} />
</div>
