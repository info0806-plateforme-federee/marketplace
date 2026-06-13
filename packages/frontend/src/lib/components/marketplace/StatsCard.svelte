<!--
@component
Tuile de métrique simple affichant une grande `value` sous un petit `label`
(utilisée sur le tableau de bord d'accueil).
-->
<script lang="ts">
    interface Props {
        label: string;
        value: string | number;
        class?: string;
    }

    let { label, value, class: className = '' }: Props = $props();
</script>

<div class="rounded-lg border border-border bg-card p-6 {className}">
    <p class="text-sm text-muted-foreground">{label}</p>
    <p class="text-3xl font-bold text-foreground mt-1">{value}</p>
</div>
