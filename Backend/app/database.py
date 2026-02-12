from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging
import os

logger = logging.getLogger(__name__)

# Create engine with connection pool settings
try:
    if settings.DATABASE_URL.startswith("sqlite"):
        # SQLite configuration
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            connect_args={
                "check_same_thread": False,  # Allow multi-threaded access
            }
        )
    elif "cloudsql" in settings.DATABASE_URL or os.getenv("INSTANCE_CONNECTION_NAME"):
        # Cloud SQL configuration with Python Connector
        try:
            from google.cloud.sql.connector import Connector
            import pg8000
            
            # Initialize Cloud SQL Python Connector
            connector = Connector()
            
            # Cloud SQL instance connection name
            instance_connection_name = "project-0990a5d7-310c-4a56-837:asia-south1:ods-database"
            
            def getconn():
                return connector.connect(
                    instance_connection_name,
                    "pg8000",
                    user="ods_user",
                    password="ods_password",
                    db="ods_db"
                )
            
            # Create engine using Cloud SQL Python Connector
            engine = create_engine(
                "postgresql+pg8000://",
                creator=getconn,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                echo=settings.DEBUG,
                pool_pre_ping=True
            )
            
            logger.info("Database engine created with Cloud SQL Python Connector")
            
        except ImportError:
            logger.warning("Cloud SQL Python Connector not available, falling back to psycopg2")
            # Fallback to psycopg2 with Unix socket
            engine = create_engine(
                settings.DATABASE_URL,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                echo=settings.DEBUG,
                pool_pre_ping=True,
                connect_args={
                    "connect_timeout": 10,
                }
            )
    else:
        # Regular PostgreSQL configuration
        engine = create_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 10,
            }
        )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

