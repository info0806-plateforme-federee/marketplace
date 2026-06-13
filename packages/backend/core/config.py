"""Configuration de l'application.

Les réglages sont chargés par Pydantic depuis les variables d'environnement (ou un
fichier `.env`) avec un délimiteur imbriqué : p. ex. `DATABASE__HOST=...`
correspond à `settings.database.host`, `GATEWAY__URL=...` à `settings.gateway.url`.
Chaque champ a une valeur par défaut, donc le service démarre aussi sans aucune
variable d'environnement.

Importer le singleton `settings` défini au niveau du module plutôt que de
reconstruire `Settings()`.
"""

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL


class DatabaseConfig(BaseModel):
    """Configuration de la base PostgreSQL."""

    host: str = "postgres"
    port: int = 5432
    user: str = "marketplace"
    password: str = "marketplace"
    name: str = "marketplace"

    @property
    def async_url(self) -> URL:
        """Construit l'URL de connexion asyncpg utilisée par le moteur asynchrone de l'app.

        Retourne :
            Une URL SQLAlchemy avec le pilote `postgresql+asyncpg`.
        """
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.name,
        )

    @property
    def sync_url(self) -> URL:
        """Construit l'URL de connexion synchrone utilisée par les migrations Alembic.

        Retourne :
            Une URL SQLAlchemy avec le pilote `postgresql` simple.
        """
        return URL.create(
            drivername="postgresql",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.name,
        )


class MarketplaceConfig(BaseModel):
    """Identité de cette instance de marketplace en tant que site fédéré.

    `site_id`/`site_name` identifient le site local qui possède les services qu'il
    publie et qui agit comme consommateur lors de l'invocation de services.
    """

    site_id: str = "site-local"
    site_name: str = "Local Site"


class GatewayConfig(BaseModel):
    """Connexion au gateway gRPC du nœud (le point d'entrée vers l'ordonnancement)."""

    url: str = "node:50052"


class FixturesConfig(BaseModel):
    """Bascules pour le seeding des services de démonstration intégrés au démarrage.

    `enabled` est l'interrupteur principal ; les drapeaux par démo sélectionnent
    lesquelles des démos fournies (nettoyage CSV, stress GPU, rendu 3D) sont seedées.
    """

    enabled: bool = True
    seed_csv_cleaning_demo: bool = True
    seed_gpu_stress_demo: bool = True
    seed_3d_render_demo: bool = True


class Settings(BaseSettings):
    """Réglages de premier niveau agrégeant chaque section de configuration.

    Chaque attribut est rempli à partir des variables d'environnement
    `<SECTION>__<CHAMP>` (p. ex. `DATABASE__PASSWORD`) grâce à
    `env_nested_delimiter`.
    """

    database: DatabaseConfig = DatabaseConfig()
    marketplace: MarketplaceConfig = MarketplaceConfig()
    gateway: GatewayConfig = GatewayConfig()
    fixtures: FixturesConfig = FixturesConfig()

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


# Singleton au niveau du module, importé dans toute l'app ; construit une fois à l'import.
settings = Settings()
