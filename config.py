from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str
    db_password: str
    db_database: str

    # -------------------------------------------------------------------------
    # Model
    # -------------------------------------------------------------------------

    model_hidden_size: int = 8
    model_num_epochs: int = 1000
    model_batch_size: int = 8
    model_learning_rate: float = 0.001

    # -------------------------------------------------------------------------
    # Paths
    # -------------------------------------------------------------------------

    project_root: Path = PROJECT_ROOT

    data_dir: Path = PROJECT_ROOT / "data"

    intents_file: Path = PROJECT_ROOT / "data" / "intents.json"

    training_data_file: Path = (
            PROJECT_ROOT / "data" / "training_data.pth"
    )

    db_initialized_file: Path = (
            PROJECT_ROOT / "data" / "db_initialized.txt"
    )

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
