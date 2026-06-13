<!--
@component
Petite étiquette en pilule. Le `variant` choisit un jeu de couleurs (p. ex.
`success`, `warning`, `destructive`) ; `children` est le texte du badge.
-->
<script lang="ts">
    import type { Snippet } from 'svelte';

    interface Props {
        variant?: 'default' | 'secondary' | 'success' | 'warning' | 'destructive' | 'outline';
        class?: string;
        children: Snippet;
    }

    let { variant = 'default', class: className = '', children }: Props = $props();

    const variantClasses = {
        default: 'bg-primary text-primary-foreground',
        secondary: 'bg-secondary text-secondary-foreground',
        success: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
        warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
        destructive: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
        outline: 'border border-border text-foreground',
    };
</script>

<span
    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {variantClasses[variant]} {className}"
>
    {@render children()}
</span>
