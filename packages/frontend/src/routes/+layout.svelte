<script lang="ts">
	import './layout.css';
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Navbar from '$lib/components/layout/Navbar.svelte';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div class="min-h-screen bg-background">
	<Navbar />
	<main class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
		{@render children()}
	</main>
</div>
