from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL


class DatabaseConfig(BaseModel):
    """PostgreSQL database configuration."""

    host: str = "postgres"
    port: int = 5432
    user: str = "marketplace"
    password: str = "marketplace"
    name: str = "marketplace"

    @property
    def async_url(self) -> URL:
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
        return URL.create(
            drivername="postgresql",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.name,
        )


class MarketplaceConfig(BaseModel):
    """Marketplace-specific configuration."""

    site_id: str = "site-local"
    site_name: str = "Local Site"


class GatewayConfig(BaseModel):
    """gRPC gateway connection configuration."""

    url: str = "node:50052"


class Settings(BaseSettings):
    database: DatabaseConfig = DatabaseConfig()
    marketplace: MarketplaceConfig = MarketplaceConfig()
    gateway: GatewayConfig = GatewayConfig()

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


settings = Settings()
