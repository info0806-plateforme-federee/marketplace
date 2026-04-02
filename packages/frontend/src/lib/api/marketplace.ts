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
// Internal helpers
// ---------------------------------------------------------------------------

/** Shape of a FastAPI validation / detail error body. */
interface ApiErrorBody {
	detail?: string | { msg: string }[];
}

function extractErrorMessage(body: ApiErrorBody, fallback: string): string {
	if (!body.detail) return fallback;
	if (typeof body.detail === 'string') return body.detail;
	// FastAPI validation errors are an array of objects with a `msg` field.
	return body.detail.map((d) => d.msg).join('; ');
}

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
// Client factory
// ---------------------------------------------------------------------------

/**
 * Creates a typed marketplace API client.
 *
 * Pass SvelteKit's `fetch` from a `load` function to keep server-side
 * requests within the same request context (cookies, SSR streaming, etc.).
 * Falls back to the global `fetch` when called client-side.
 *
 * @param fetchFn  - The fetch implementation to use (default: global fetch).
 * @param baseUrl  - Root URL of the marketplace API service.
 */
export function createMarketplaceClient(
	fetchFn: typeof fetch = fetch,
	baseUrl = 'http://localhost:8090'
) {
	// -------------------------------------------------------------------------
	// Core request helper
	// -------------------------------------------------------------------------

	async function request<T>(path: string, options?: RequestInit): Promise<T> {
		const url = `${baseUrl}/api${path}`;
		const res = await fetchFn(url, {
			headers: {
				'Content-Type': 'application/json',
				...options?.headers,
			},
			...options,
		});

		// 204 No Content — nothing to parse.
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
	// Public API surface
	// -------------------------------------------------------------------------

	return {
		// -- Sites ---------------------------------------------------------------

		getSites(): Promise<Site[]> {
			return request<Site[]>('/sites');
		},

		getSite(id: string): Promise<Site> {
			return request<Site>(`/sites/${id}`);
		},

		createSite(data: CreateSiteRequest): Promise<Site> {
			return request<Site>('/sites', {
				method: 'POST',
				body: JSON.stringify(data),
			});
		},

		// -- Services ------------------------------------------------------------

		getServices(filters: ServiceFilters = {}): Promise<PaginatedResponse<ServiceSummary>> {
			const qs = buildQueryString(filters as Record<string, unknown>);
			return request<PaginatedResponse<ServiceSummary>>(`/services${qs}`);
		},

		getService(slug: string, includePrivate = false): Promise<Service> {
			const qs = includePrivate ? '?include_private=true' : '';
			return request<Service>(`/services/${slug}${qs}`);
		},

		createService(data: CreateServiceRequest): Promise<Service> {
			return request<Service>('/services', {
				method: 'POST',
				body: JSON.stringify(data),
			});
		},

		updateService(slug: string, data: UpdateServiceRequest): Promise<Service> {
			return request<Service>(`/services/${slug}`, {
				method: 'PATCH',
				body: JSON.stringify(data),
			});
		},

		deleteService(slug: string): Promise<void> {
			return request<void>(`/services/${slug}`, { method: 'DELETE' });
		},

		getServicePricing(slug: string): Promise<ServicePricing> {
			return request<ServicePricing>(`/services/${slug}/pricing`);
		},

		// -- Invocations ---------------------------------------------------------

		invokeService(slug: string, data: InvokeServiceRequest): Promise<Invocation> {
			return request<Invocation>(`/services/${slug}/invoke`, {
				method: 'POST',
				body: JSON.stringify(data),
			});
		},

		getInvocations(filters: InvocationFilters = {}): Promise<PaginatedResponse<Invocation>> {
			const qs = buildQueryString(filters as Record<string, unknown>);
			return request<PaginatedResponse<Invocation>>(`/invocations${qs}`);
		},

		getInvocation(id: string): Promise<Invocation> {
			return request<Invocation>(`/invocations/${id}`);
		},

		getInvocationResult(id: string): Promise<InvocationResult> {
			return request<InvocationResult>(`/invocations/${id}/result`);
		},
	};
}

/** Convenience type alias for the client object returned by the factory. */
export type MarketplaceClient = ReturnType<typeof createMarketplaceClient>;
