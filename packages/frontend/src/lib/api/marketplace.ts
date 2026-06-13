/**
 * Client HTTP typé pour l'API REST du backend de la marketplace.
 *
 * `createMarketplaceClient` renvoie un objet dont les méthodes correspondent 1:1
 * aux endpoints du backend (sites, services, invocations). Toutes les requêtes
 * passent par une unique fonction `request` qui préfixe `/api`, pose les en-têtes
 * JSON, déballe les 204, et transforme les réponses non-OK en `Error` levées
 * portant le message de détail du backend. Passer le `fetch` scopé de SvelteKit
 * depuis les fonctions `load` pour le SSR.
 */
import type {
	Site,
	Service,
	ServiceSummary,
	ServicePricing,
	ServiceFilters,
	CreateServiceRequest,
	UpdateServiceRequest,
	Invocation,
	InvocationResult,
	InvocationFilters,
	InvokeServiceRequest,
	CreateSiteRequest,
	PaginatedResponse,
} from '$lib/types/marketplace';

// ---------------------------------------------------------------------------
// Aides internes
// ---------------------------------------------------------------------------

/** Forme d'un corps d'erreur de validation / détail FastAPI. */
interface ApiErrorBody {
	detail?: string | { msg: string }[];
}

/**
 * Aplatit un corps d'erreur FastAPI en un seul message lisible.
 *
 * @param body     - Réponse d'erreur parsée (`detail` peut être une chaîne ou un
 *                    tableau d'erreurs de validation).
 * @param fallback - Message à utiliser quand aucun `detail` n'est présent.
 * @returns La chaîne de détail, les messages de validation joints, ou le fallback.
 */
function extractErrorMessage(body: ApiErrorBody, fallback: string): string {
	if (!body.detail) return fallback;
	if (typeof body.detail === 'string') return body.detail;
	// Les erreurs de validation FastAPI sont un tableau d'objets avec un champ `msg`.
	return body.detail.map((d) => d.msg).join('; ');
}

/**
 * Construit une chaîne de requête URL depuis un objet de params, en ignorant les valeurs vides.
 *
 * @param params - Paires clé/valeur ; `undefined`, `null` et `''` sont omis.
 * @returns Une chaîne de requête préfixée par `?`, ou `''` s'il ne reste aucun param.
 */
function buildQueryString(params: Record<string, unknown>): string {
	const qs = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined && value !== null && value !== '') {
			qs.set(key, String(value));
		}
	}
	const str = qs.toString();
	return str ? `?${str}` : '';
}

// ---------------------------------------------------------------------------
// Fabrique de client
// ---------------------------------------------------------------------------

/**
 * Crée un client typé pour l'API de la marketplace.
 *
 * Passer le `fetch` de SvelteKit depuis une fonction `load` pour garder les
 * requêtes côté serveur dans le même contexte de requête (cookies, streaming SSR,
 * etc.). Se rabat sur le `fetch` global lorsqu'appelé côté client.
 *
 * @param fetchFn  - L'implémentation de fetch à utiliser (défaut : fetch global).
 * @param baseUrl  - URL racine du service API de la marketplace.
 */
export function createMarketplaceClient(
	fetchFn: typeof fetch = fetch,
	baseUrl = 'http://localhost:8090'
) {
	// -------------------------------------------------------------------------
	// Fonction de requête centrale
	// -------------------------------------------------------------------------

	/**
	 * Émet une requête vers `{baseUrl}/api{path}` et parse la réponse JSON.
	 *
	 * @param path    - Chemin d'API commençant par `/` (p. ex. `/services`).
	 * @param options - Init fetch optionnel (méthode, corps, en-têtes additionnels).
	 * @returns Le JSON parsé en `T`, ou `undefined` pour les réponses 204.
	 * @throws Error portant le message de détail du backend sur réponse non-OK.
	 */
	async function request<T>(path: string, options?: RequestInit): Promise<T> {
		const url = `${baseUrl}/api${path}`;
		const res = await fetchFn(url, {
			headers: {
				'Content-Type': 'application/json',
				...options?.headers,
			},
			...options,
		});

		// 204 No Content — rien à parser.
		if (res.status === 204) {
			return undefined as T;
		}

		if (!res.ok) {
			const body: ApiErrorBody = await res.json().catch(() => ({}));
			throw new Error(extractErrorMessage(body, `API error: ${res.status}`));
		}

		return res.json() as Promise<T>;
	}

	// -------------------------------------------------------------------------
	// Surface d'API publique
	// -------------------------------------------------------------------------

	return {
		// -- Sites ---------------------------------------------------------------

		/** Liste tous les sites fédérés enregistrés. */
		getSites(): Promise<Site[]> {
			return request<Site[]>('/sites');
		},

		/** Récupère un site unique par son ID. */
		getSite(id: string): Promise<Site> {
			return request<Site>(`/sites/${id}`);
		},

		/** Enregistre un nouveau site fédéré. */
		createSite(data: CreateSiteRequest): Promise<Site> {
			return request<Site>('/sites', {
				method: 'POST',
				body: JSON.stringify(data),
			});
		},

		// -- Services ------------------------------------------------------------

		/** Liste/recherche les services ; `filters` deviennent des params de requête. Renvoie une page. */
		getServices(filters: ServiceFilters = {}): Promise<PaginatedResponse<ServiceSummary>> {
			const qs = buildQueryString(filters as Record<string, unknown>);
			return request<PaginatedResponse<ServiceSummary>>(`/services${qs}`);
		},

		/** Récupère un service par slug ; mettre `includePrivate` pour contourner le filtre public. */
		getService(slug: string, includePrivate = false): Promise<Service> {
			const qs = includePrivate ? '?include_private=true' : '';
			return request<Service>(`/services/${slug}${qs}`);
		},

		/** Publie un nouveau service au catalogue. */
		createService(data: CreateServiceRequest): Promise<Service> {
			return request<Service>('/services', {
				method: 'POST',
				body: JSON.stringify(data),
			});
		},

		/** Met à jour partiellement un service identifié par slug. */
		updateService(slug: string, data: UpdateServiceRequest): Promise<Service> {
			return request<Service>(`/services/${slug}`, {
				method: 'PATCH',
				body: JSON.stringify(data),
			});
		},

		/** Supprime en douceur (désactive) un service par slug. Se résout sur 204. */
		deleteService(slug: string): Promise<void> {
			return request<void>(`/services/${slug}`, { method: 'DELETE' });
		},

		/** Récupère les détails de tarification d'un service par slug. */
		getServicePricing(slug: string): Promise<ServicePricing> {
			return request<ServicePricing>(`/services/${slug}/pricing`);
		},

		// -- Invocations ---------------------------------------------------------

		/** Invoque un service par slug avec le payload d'entrée fourni. */
		invokeService(slug: string, data: InvokeServiceRequest): Promise<Invocation> {
			return request<Invocation>(`/services/${slug}/invoke`, {
				method: 'POST',
				body: JSON.stringify(data),
			});
		},

		/** Liste les invocations ; `filters` deviennent des params de requête. Renvoie une page. */
		getInvocations(filters: InvocationFilters = {}): Promise<PaginatedResponse<Invocation>> {
			const qs = buildQueryString(filters as Record<string, unknown>);
			return request<PaginatedResponse<Invocation>>(`/invocations${qs}`);
		},

		/** Récupère une invocation unique par ID (le statut est auto-rafraîchi côté serveur). */
		getInvocation(id: string): Promise<Invocation> {
			return request<Invocation>(`/invocations/${id}`);
		},

		/** Récupère le résumé de résultat (statut, URLs, coût final) d'une invocation. */
		getInvocationResult(id: string): Promise<InvocationResult> {
			return request<InvocationResult>(`/invocations/${id}/result`);
		},
	};
}

/** Alias de type pratique pour l'objet client renvoyé par la fabrique. */
export type MarketplaceClient = ReturnType<typeof createMarketplaceClient>;
