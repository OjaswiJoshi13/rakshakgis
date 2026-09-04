import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# RakshakGIS Application Imports
from app.core.config import get_settings
from app.core.database import Base
# Import all models so Base.metadata is fully populated
import app.models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# Set SQLAlchemy target metadata to RakshakGIS Base.metadata
target_metadata = Base.metadata

# Override sqlalchemy.url with dynamic application settings
settings = get_settings()
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

POSTGIS_SYSTEM_TABLES = {
    "spatial_ref_sys",
    "layer",
    "topology",
    "geocode_settings",
    "geocode_settings_default",
    "loader_platform",
    "loader_variables",
    "loader_lookuptables",
    "direction_lookup",
    "secondary_unit_lookup",
    "state_lookup",
    "street_type_lookup",
    "county_lookup",
    "countysub_lookup",
    "zip_lookup",
    "zip_lookup_all",
    "zip_lookup_base",
    "zip_state",
    "zip_state_loc",
    "addr",
    "addrfeat",
    "bg",
    "county",
    "cousub",
    "edges",
    "faces",
    "featnames",
    "pagc_gaz",
    "pagc_lex",
    "pagc_rules",
    "place",
    "place_lookup",
    "state",
    "tabblock",
    "tabblock20",
    "tract",
    "zcta5",
}


def include_object(object, name, type_, reflected, compare_to):
    """Filter out PostGIS extensions and system tables from autogenerate comparisons."""
    if type_ == "table" and reflected and compare_to is None:
        if (
            name in POSTGIS_SYSTEM_TABLES
            or name.startswith("tiger_")
            or name.startswith("topology_")
            or name.startswith("loader_")
        ):
            return False
    if type_ == "table" and (
        name in POSTGIS_SYSTEM_TABLES
        or name.startswith("tiger_")
        or name.startswith("topology_")
        or name.startswith("loader_")
    ):
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
