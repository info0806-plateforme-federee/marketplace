/**
 * Miroir TypeScript du contrat d'API du backend de la marketplace.
 *
 * Ces types correspondent aux schémas Pydantic du backend (les noms de champs en
 * snake_case sont conservés pour que le JSON se désérialise directement). Les
 * garder synchronisés avec `packages/backend/schemas/` et les enums du modèle.
 * Regroupés ci-dessous en : enums chaîne, entités principales, payloads de
 * requête/filtre, et l'enveloppe de pagination.
 */

// ---------------------------------------------------------------------------
// Enums (types union de littéraux de chaîne)
// ---------------------------------------------------------------------------

export type SiteStatus = 'active' | 'inactive' | 'pending';

export type ServiceStatus = 'active' | 'disabled' | 'draft' | 'deprecated';

export type ServiceType = 'compute' | 'data' | 'model' | 'utility';

export type PriceType = 'free' | 'fixed' | 'time';

export type ExecutionMode = 'sync' | 'async';

export type Visibility = 'public' | 'private' | 'restricted';

export type InvocationStatus =
	| 'pending'
	| 'accepted'
	| 'running'
	| 'succeeded'
	| 'failed'
	| 'cancelled';

// ---------------------------------------------------------------------------
// Entités principales
// ---------------------------------------------------------------------------

export interface Site {
	id: string;
	name: string;
	description: string | null;
	grpc_endpoint: string | null;
	status: SiteStatus;
	trusted: boolean;
	created_at: string;
	updated_at: string;
}

export interface Service {
	id: string;
	provider_site_id: string;
	name: string;
	slug: string;
	description: string | null;
	category: string;
	tags: string[];
	service_type: ServiceType;
	version: string;
	status: ServiceStatus;
	price_type: PriceType;
	price_amount: number | null;
	currency: string;
	visibility: Visibility;
	execution_mode: ExecutionMode;
	input_schema: Record<string, unknown>;
	output_schema: Record<string, unknown>;
	max_concurrency: number | null;
	timeout_s: number | null;
	terms_of_use: string | null;
	created_at: string;
	updated_at: string;
	provider_site: Site | null;
}

export interface ServiceSummary {
	id: string;
	name: string;
	slug: string;
	description: string | null;
	category: string;
	tags: string[];
	service_type: ServiceType;
	price_type: PriceType;
	price_amount: number | null;
	currency: string;
	status: ServiceStatus;
	provider_site: { id: string; name: string } | null;
}

export interface ServicePricing {
	price_type: PriceType;
	price_amount: number | null;
	currency: string;
}

export interface Invocation {
	id: string;
	service_id: string;
	provider_site_id: string;
	consumer_site_id: string;
	status: InvocationStatus;
	input_payload: Record<string, unknown>;
	result_url: string | null;
	artifact_url: string | null;
	error_message: string | null;
	cost_estimated: number | null;
	cost_final: number | null;
	currency: string;
	started_at: string | null;
	ended_at: string | null;
	created_at: string;
}

export interface InvocationResult {
	status: InvocationStatus;
	result_url: string | null;
	artifact_url: string | null;
	error_message: string | null;
	cost_final: number | null;
}

// ---------------------------------------------------------------------------
// Types de requête / filtre
// ---------------------------------------------------------------------------

export interface CreateServiceRequest {
	name: string;
	description?: string;
	category: string;
	tags?: string[];
	service_type: ServiceType;
	version?: string;
	status?: ServiceStatus;
	price_type: PriceType;
	price_amount?: number | null;
	currency?: string;
	visibility: Visibility;
	execution_mode: ExecutionMode;
	input_schema?: Record<string, unknown>;
	output_schema?: Record<string, unknown>;
	max_concurrency?: number | null;
	timeout_s?: number | null;
	terms_of_use?: string | null;
}

export type UpdateServiceRequest = Partial<CreateServiceRequest>;

export interface InvokeServiceRequest {
	input_payload: Record<string, unknown>;
}

export interface ServiceFilters {
	search?: string;
	category?: string;
	service_type?: ServiceType;
	price_type?: PriceType;
	provider_site_id?: string;
	status?: ServiceStatus;
	visibility?: Visibility;
	page?: number;
	per_page?: number;
}

export interface InvocationFilters {
	status?: InvocationStatus;
	service_id?: string;
	page?: number;
	per_page?: number;
}

export interface CreateSiteRequest {
	name: string;
	description?: string;
	grpc_endpoint?: string;
	trusted?: boolean;
}

// ---------------------------------------------------------------------------
// Enveloppe de pagination
// ---------------------------------------------------------------------------

export interface PaginatedResponse<T> {
	items: T[];
	total: number;
	page: number;
	per_page: number;
	total_pages: number;
}
