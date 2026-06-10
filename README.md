# Marketplace — Publication et invocation de services

La **marketplace** permet de publier des services (une image/du code + une
configuration d'exécution) et de les *invoquer* à la demande. Chaque invocation
est traduite en *job* envoyé au **nœud**, qui l'attribue à un worker. L'interface
web suit l'avancement et permet de récupérer les artefacts produits.

> Prérequis fonctionnel : le **nœud** doit être démarré et joignable sur le
> tailnet **avant** d'invoquer un service (sinon les invocations resteront en
> attente). Voir `../node/README.md`.

## Rôle dans la plateforme

```
 Navigateur ──HTTP──► Frontend SvelteKit (localhost:3005)
                          │  (rendu serveur → backend)
                          ▼
                      Backend FastAPI (localhost:8090)
                          │  gRPC InvokeService
                          ▼
                      Gateway du nœud (node:50052, via tailnet)
```

La marketplace est une pile Compose **distincte** du nœud, avec sa **propre base
PostgreSQL**. La communication avec le nœud passe par Tailscale (le backend tourne
dans le *network namespace* du sidecar `tailscale` et joint `node:50052`).

## Composants (services Compose)

| Service     | Rôle                                                       | Accès |
|-------------|------------------------------------------------------------|-------|
| `frontend`  | Interface web SvelteKit                                    | `localhost:3005` |
| `backend`   | API REST (services, invocations, WebSocket de statut), migrations Alembic, fixtures démo | `localhost:8090` |
| `postgres`  | Base de données de la marketplace                          | `localhost:5435` |
| `tailscale` | Sidecar tailnet ; publie le port du backend en `8090`      | — |

> Le backend utilise `network_mode: service:tailscale`. C'est donc le conteneur
> `tailscale` qui expose `8090:8080` — d'où l'accès au backend via
> `http://localhost:8090`.

## Prérequis

- **Docker** et **Docker Compose v2**.
- Le **nœud déjà initialisé** et connecté au tailnet (`TS_HOSTNAME=node`).
- Une **clé d'auth Tailscale** (`tskey-auth-…`) — la même tailnet que le nœud.
- *(Optionnel, pour le développement frontend en local)* **Node.js 22+** et npm.

## Initialisation — pas à pas

1. **Créer le fichier d'environnement** :

   ```bash
   cd marketplace
   cp .env.example .env
   ```

2. **Renseigner `.env`** :

   ```dotenv
   TS_AUTHKEY=tskey-auth-xxxxx                       # clé Tailscale (même tailnet que le nœud)
   TS_HOSTNAME=marketplace                           # nom sur le tailnet
   GATEWAY_URL=node:50052                            # gateway gRPC du nœud
   PUBLIC_MARKETPLACE_API_URL=http://localhost:8090  # URL du backend vue par le navigateur
   ```

3. **Démarrer la pile** :

   ```bash
   docker compose up -d --build
   ```

   Au démarrage, **rien à faire manuellement** :
   - le `backend` applique automatiquement les migrations Alembic
     (`alembic upgrade head`) ;
   - les **fixtures de démonstration** sont semées par défaut
     (`FIXTURES__ENABLED=true`), ce qui crée les services `csv-cleaning-demo` et
     `gpu-stress-benchmark` et `3d-render-demo` (avec leur configuration
     d'exécution enregistrée auprès du nœud).

4. **Vérifier** :

   ```bash
   docker compose ps                       # tous "healthy" / "running"
   curl http://localhost:8090/healthz      # -> {"status":"ok"} attendu
   ```

   - Interface web : <http://localhost:3005>
   - Documentation de l'API backend : <http://localhost:8090/docs>

5. **Bout en bout** : pour qu'une invocation aboutisse, démarrez au moins un
   **worker** (voir `../worker/README.md`). Les scripts de smoke test à la racine
   du dépôt (`test_csv_cleaning_service.py`, `test_gpu_stress_service.py`)
   permettent de valider la chaîne complète.

## Développement du frontend en local (hors Docker)

```bash
cd packages/frontend
npm install
npm run dev        # serveur de dev (Vite) avec rechargement à chaud
npm run build      # build de production
npm run lint       # eslint + prettier
npm run format     # auto-formatage
```

Définissez `MARKETPLACE_API_URL=http://localhost:8090` dans l'environnement du
frontend local pour cibler le backend conteneurisé. Voir

## Variables d'environnement

| Variable                     | Où             | Défaut                   | Description |
|------------------------------|----------------|--------------------------|-------------|
| `TS_AUTHKEY`                 | `.env`         | —                        | **Obligatoire.** Clé d'auth Tailscale. |
| `TS_HOSTNAME`                | `.env`         | `marketplace`            | Nom d'hôte sur le tailnet. |
| `GATEWAY_URL`                | `.env`         | `node:50052`             | Gateway gRPC du nœud (sur le tailnet). |
| `PUBLIC_MARKETPLACE_API_URL` | `.env`         | `http://localhost:8090`  | URL du backend **vue par le navigateur** (suivi WebSocket/statut). |
| `MARKETPLACE_API_URL`        | `compose.yaml` | `http://tailscale:8080`  | URL backend pour le rendu serveur du frontend. |
| `INTERNAL_API_KEY`           | `compose.yaml` | *(fournie)*              | Clé d'API interne frontend → backend. |
| `DATABASE__*`                | `compose.yaml` | `marketplace`            | Connexion PostgreSQL. |
| `MARKETPLACE__SITE_ID/NAME`  | `compose.yaml` | `site-local` / `Local Site` | Identité du site marketplace. |
| `FIXTURES__ENABLED`          | code (défaut)  | `true`                   | Semence les services de démonstration au démarrage. |
| `FIXTURES__SEED_3D_RENDER_DEMO` | code (défaut) | `true`                | Active la fixture `3d-render-demo`. |
| `UID` / `GID`                | env hôte (opt.)| `1000`                   | UID/GID dans les conteneurs. |

Configuration via **Pydantic Settings**, délimiteur `__` (ex. `DATABASE__HOST`,
`MARKETPLACE__SITE_ID`).

## Production

Un fichier `compose.prod.yaml` est fourni : il bâtit le frontend avec
`docker/frontend.prod.Dockerfile` (build statique servi en production) au lieu du
serveur de dev.

```bash
docker compose -f compose.prod.yaml up -d --build
```

## Commandes utiles

```bash
docker compose up -d --build      # (re)construire et démarrer
docker compose logs -f backend    # suivre les logs du backend
docker compose down               # arrêter (les données persistent)
docker compose down -v            # arrêter ET réinitialiser la base

# Migrations (normalement automatiques au démarrage du backend) :
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade -1
```

## Ports

| Service              | Conteneur | Hôte     |
|----------------------|-----------|----------|
| Frontend             | 3000      | **3005** |
| Backend (via tailscale) | 8080   | **8090** |
| PostgreSQL           | 5432      | **5435** |

## Dépannage

- **Les invocations restent « pending »** : aucun worker n'est connecté, ou le
  nœud est injoignable. Vérifiez que le nœud tourne, qu'un worker est enregistré
  et que les trois piles partagent le même tailnet (`tailscale status`).
- **Le backend ne joint pas le gateway** : contrôlez `GATEWAY_URL=node:50052` et
  que `node` est résolu sur le tailnet depuis le conteneur `tailscale`.
- **Le frontend n'affiche pas les mises à jour de statut** : vérifiez que
  `PUBLIC_MARKETPLACE_API_URL` pointe vers une URL joignable par le navigateur
  (`http://localhost:8090` en local).

> Note : les stubs gRPC du gateway sont déjà versionnés dans
> `packages/backend/gateway_stubs/`. La régénération des `.proto` se fait depuis
> le nœud (`make proto` dans `../node`), source de vérité des définitions proto.
