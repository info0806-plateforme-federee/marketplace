<!--
@component
Champ de recherche avec une icône en tête qui appelle `onsearch` avec le texte
courant, déboucé de 300 ms pour que la frappe ne déclenche pas une requête à
chaque touche.
-->
<script lang="ts">
    interface Props {
        value?: string;
        placeholder?: string;
        class?: string;
        onsearch: (value: string) => void;
    }

    let { value = '', placeholder = 'Search...', class: className = '', onsearch }: Props = $props();

    let timeout: ReturnType<typeof setTimeout>;

    /** Débounce de la saisie : n'émet la dernière valeur que 300 ms après l'arrêt de la frappe. */
    function handleInput(e: Event) {
        const target = e.target as HTMLInputElement;
        clearTimeout(timeout);
        timeout = setTimeout(() => onsearch(target.value), 300);
    }
</script>

<div class="relative {className}">
    <svg
        class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
        aria-hidden="true"
    >
        <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
    </svg>
    <input
        type="text"
        {value}
        {placeholder}
        oninput={handleInput}
        aria-label={placeholder}
        class="flex h-10 w-full rounded-md border border-input bg-surface pl-10 pr-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    />
</div>
