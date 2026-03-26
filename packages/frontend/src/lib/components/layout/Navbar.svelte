<script lang="ts">
    import { page } from '$app/state';
    import { theme } from '$lib/theme.svelte';
    import { locales, localizeHref, getLocale, setLocale } from '$lib/paraglide/runtime';
    import * as m from '$lib/paraglide/messages';

    let mobileOpen = $state(false);

    const links = $derived([
        { href: localizeHref('/'), label: m.nav_home() },
        { href: localizeHref('/services'), label: m.nav_catalog() },
        { href: localizeHref('/services/publish'), label: m.nav_publish() },
        { href: localizeHref('/services/mine'), label: m.nav_my_services() },
        { href: localizeHref('/invocations'), label: m.nav_invocations() },
    ]);

    let locale = $state(getLocale());

    function isActive(href: string): boolean {
        const path = page.url.pathname;
        if (href === '/') return path === '/';
        return path === href;
    }

    function toggleLocale() {
        const next = locale === 'fr' ? 'en' : 'fr';
        locale = next;
        setLocale(next);
    }
</script>

<nav class="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 items-center justify-between">
            <!-- Brand -->
            <a href={localizeHref('/')} class="text-xl font-bold font-title text-foreground">
                Marketplace
            </a>

            <!-- Desktop nav -->
            <div class="hidden md:flex items-center gap-1">
                {#each links as link}
                    <a
                        href={link.href}
                        class="px-3 py-2 rounded-md text-sm font-medium transition-colors {isActive(link.href) ? 'bg-accent/10 text-accent' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}"
                    >
                        {link.label}
                    </a>
                {/each}
            </div>

            <!-- Right side -->
            <div class="flex items-center gap-2">
                <!-- Locale switcher -->
                <div class="flex items-center gap-1">
                    {#each locales as locale}
                        <button
                                onclick={() => setLocale(locale)}
                                class="px-2 py-1 rounded text-xs font-medium uppercase transition-colors {getLocale() === locale ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}"
                        >
                            {locale}
                        </button>
                    {/each}
                </div>

                <!-- Dark mode toggle -->
                <button
                    onclick={() => theme.toggle()}
                    class="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    aria-label={m.dark_mode_toggle()}
                >
                    {#if theme.dark}
                        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                        </svg>
                    {:else}
                        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                        </svg>
                    {/if}
                </button>

                <!-- Mobile hamburger -->
                <button
                    onclick={() => (mobileOpen = !mobileOpen)}
                    class="md:hidden p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted"
                    aria-label="Toggle menu"
                >
                    <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        {#if mobileOpen}
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                        {:else}
                            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                        {/if}
                    </svg>
                </button>
            </div>
        </div>

        <!-- Mobile nav -->
        {#if mobileOpen}
            <div class="md:hidden pb-4 space-y-1">
                {#each links as link}
                    <a
                        href={link.href}
                        onclick={() => (mobileOpen = false)}
                        class="block px-3 py-2 rounded-md text-sm font-medium {isActive(link.href) ? 'bg-accent/10 text-accent' : 'text-muted-foreground hover:text-foreground hover:bg-muted'}"
                    >
                        {link.label}
                    </a>
                {/each}
            </div>
        {/if}
    </div>
</nav>
