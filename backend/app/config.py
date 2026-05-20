from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore" so OS-level vars like SSL_CERT_FILE in .env don't cause
    # validation errors — they're consumed by the runtime, not the app config
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase — or any Postgres-compatible REST endpoint that speaks the PostgREST protocol.
    # See README § "Alternative databases" if you're not using Supabase.
    supabase_url: str
    supabase_service_role_key: str

    # Optional NVD API key — increases rate limit from ~5 to 50 req/30s
    nvd_api_key: str = ""

    # Cron expressions (UTC). Defaults match the values in .env.example.
    cisa_kev_cron: str = "0 6 * * *"
    cisa_advisories_cron: str = "0 */6 * * *"
    ncsc_cron: str = "0 */6 * * *"
    nvd_cron: str = "0 7 * * *"

    log_level: str = "INFO"


settings = Settings()
