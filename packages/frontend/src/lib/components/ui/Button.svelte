<!--
@component
Bouton réutilisable. Rend un `<a>` quand `href` est fourni, sinon un `<button>`.
Les classes Tailwind sont composées depuis les props `variant` et `size` (plus
toute `class` supplémentaire). Le snippet requis `children` est le libellé du bouton.
-->
<script lang="ts">
    import type { Snippet } from 'svelte';

    interface Props {
        variant?: 'primary' | 'secondary' | 'destructive' | 'ghost' | 'outline';
        size?: 'sm' | 'md' | 'lg';
        type?: 'button' | 'submit' | 'reset';
        disabled?: boolean;
        href?: string;
        class?: string;
        onclick?: (e: MouseEvent) => void;
        children: Snippet;
    }

    let {
        variant = 'primary',
        size = 'md',
        type = 'button',
        disabled = false,
        href,
        class: className = '',
        onclick,
        children,
    }: Props = $props();

    const baseClasses =
        'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 rounded-md';

    const variantClasses = {
        primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive: 'bg-destructive text-white hover:bg-destructive/90',
        ghost: 'hover:bg-accent/10 text-foreground',
        outline: 'border border-border bg-transparent hover:bg-accent/10 text-foreground',
    };

    const sizeClasses = {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-6 text-base',
    };

    let classes = $derived(`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`);
</script>

{#if href}
    <a {href} class={classes}>
        {@render children()}
    </a>
{:else}
    <button {type} {disabled} {onclick} class={classes}>
        {@render children()}
    </button>
{/if}
