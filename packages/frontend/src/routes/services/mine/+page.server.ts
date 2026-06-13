/**
 * Loader de la page « Mes services ».
 *
 * Liste les services possédés par ce site, y compris les non-publics et
 * non-actifs (en passant status/visibility à `undefined` pour contourner les
 * filtres par défaut), afin qu'un fournisseur puisse gérer tout son catalogue.
 */
import type { PageServerLoad } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env } from '$env/dynamic/private';

export const load: PageServerLoad = async ({ fetch }) => {
	const client = createMarketplaceClient(fetch, env.MARKETPLACE_API_URL ?? 'http://localhost:8090');

	// Récupère tous les services (y compris non-publics, tous statuts) du site courant.
	// L'API n'affiche par défaut que actif+public ; passer des filtres undefined
	// récupère tout ce qui est disponible pour ce nœud.
	const services = await client.getServices({
		status: undefined,
		visibility: undefined,
		per_page: 50
	});

	return { services };
};
