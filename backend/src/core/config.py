from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Front Office Analytics Platform"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, description="Debug mode")
    
    api_prefix: str = "/api/v1"
    
    database_url: str = Field(
        default="postgresql+asyncpg://fo_user:fo_password@localhost:5432/fo_analytics",
        description="PostgreSQL connection string"
    )
    
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT tokens"
    )
    
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days"
    )
    
    upload_dir: str = Field(
        default="./uploads",
        description="Directory for uploaded files"
    )
    
    # MinIO/S3 Configuration
    minio_endpoint: str = Field(
        default="localhost:9000",
        description="MinIO/S3 endpoint"
    )
    
    minio_access_key: str = Field(
        default="minioadmin",
        description="MinIO/S3 access key"
    )
    
    minio_secret_key: str = Field(
        default="minioadmin",
        description="MinIO/S3 secret key"
    )
    
    minio_bucket_name: str = Field(
        default="fo-analytics-documents",
        description="MinIO/S3 bucket name for document storage"
    )
    
    minio_use_ssl: bool = Field(
        default=False,
        description="Use SSL for MinIO/S3 connection"
    )
    
    minio_region: str = Field(
        default="us-east-1",
        description="MinIO/S3 region"
    )
    
    max_upload_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="Maximum file upload size in bytes"
    )
    
    allowed_file_extensions: list[str] = Field(
        default=[".pdf", ".txt", ".doc", ".docx"],
        description="Allowed file extensions for upload"
    )
    
    # LLM Provider Configuration
    llm_provider: str = Field(
        default="anthropic",
        description="LLM provider to use (anthropic, openai, gemini)"
    )
    
    llm_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model to use for the selected provider"
    )
    
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation"
    )
    
    llm_max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens for LLM generation"
    )
    
    llm_timeout: int = Field(
        default=60,
        gt=0,
        description="Timeout in seconds for LLM API calls"
    )
    
    # API Keys for LLM providers (use environment variables)
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key"
    )
    
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google API key for Gemini"
    )
    
    # RabbitMQ Configuration
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        description="RabbitMQ connection URL"
    )
    
    rabbitmq_exchange: str = Field(
        default="fo_analytics",
        description="RabbitMQ exchange name"
    )
    
    rabbitmq_document_queue: str = Field(
        default="document_processing",
        description="Queue name for document processing"
    )
    
    rabbitmq_dead_letter_queue: str = Field(
        default="document_processing_dlq",
        description="Dead letter queue for failed messages"
    )
    
    rabbitmq_max_retries: int = Field(
        default=3,
        description="Maximum number of message retries"
    )
    
    rabbitmq_prefetch_count: int = Field(
        default=1,
        description="Number of messages to prefetch per consumer"
    )
    
    # Backtesting Configuration
    backtest_workers: int = Field(
        default=4,
        description="Number of thread pool workers for backtesting"
    )
    
    rabbitmq_backtest_queue: str = Field(
        default="backtest_processing",
        description="Queue name for backtest processing"
    )
    
    rabbitmq_backtest_dlq: str = Field(
        default="backtest_processing_dlq",
        description="Dead letter queue for failed backtests"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()