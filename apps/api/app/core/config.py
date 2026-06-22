from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "NJUPoly API"
    app_version: str = "0.1.0"
    database_url: str
    cors_origins: str
    admin_student_ids: str = "251502013"
    session_token_secret: str = "local-dev-session-secret"
    session_token_ttl_days: int = 30
    verification_code_ttl_minutes: int = 10
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: int = 3
    media_storage_dir: str = ".local/media"
    media_public_base_url: str = "/media"

    @cached_property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @cached_property
    def safe_database_label(self) -> str:
        return self.database_url.rsplit("@", maxsplit=1)[-1]

    @cached_property
    def admin_student_id_set(self) -> set[str]:
        return {student_id.strip() for student_id in self.admin_student_ids.split(",") if student_id.strip()}

    @cached_property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)


settings = Settings()
