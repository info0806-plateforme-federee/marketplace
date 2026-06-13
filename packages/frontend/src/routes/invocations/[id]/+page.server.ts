/**
 * Loader de la page de détail d'une invocation.
 *
 * Charge l'invocation (404 si absente) et dérive aussi une URL WebSocket
 * *joignable par le navigateur* pour les mises à jour de statut en direct. Le
 * `MARKETPLACE_API_URL` privé est utilisé pour le fetch côté serveur, tandis que
 * l'URL publique (ou l'hôte courant) est utilisée pour l'endpoint WS auquel le
 * navigateur se connectera — son schéma est promu en ws/wss pour correspondre à
 * http/https.
 */
import type { PageServerLoad } from './$types';
import { createMarketplaceClient } from '$lib/api';
import { env as privateEnv } from '$env/dynamic/private';
import { env as publicEnv } from '$env/dynamic/public';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ fetch, params, url }) => {
	const apiUrl = privateEnv.MARKETPLACE_API_URL ?? 'http://localhost:8090';
	const client = createMarketplaceClient(fetch, apiUrl);

	try {
		const invocation = await client.getInvocation(params.id);
		// URL de base publique joignable par le navigateur (l'hôte interne serveur peut différer).
		const publicApiUrl =
			publicEnv.PUBLIC_MARKETPLACE_API_URL ?? `${url.protocol}//${url.hostname}:8090`;
		const wsUrl = new URL(`/api/invocations/${params.id}/ws`, publicApiUrl);
		// Aligne le schéma WS sur celui de la page (https -> wss, http -> ws).
		wsUrl.protocol = wsUrl.protocol === 'https:' ? 'wss:' : 'ws:';
		return { invocation, wsUrl: wsUrl.toString(), apiBaseUrl: publicApiUrl };
	} catch {
		error(404, 'Invocation not found');
	}
};
