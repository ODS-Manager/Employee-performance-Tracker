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
        logger.info("Database engine created with SQLite")
    else:
        # PostgreSQL configuration - try multiple approaches
        connection_successful = False
        
        # Approach 1: Direct psycopg2 connection with Unix socket
        try:
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
            # Test the connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Database engine created with psycopg2 Unix socket")
            connection_successful = True
        except Exception as e:
            logger.warning(f"psycopg2 Unix socket failed: {e}")
            
        # Approach 2: Cloud SQL Python Connector (if psycopg2 failed)
        if not connection_successful:
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
                
                # Test the connection
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
                logger.info("Database engine created with Cloud SQL Python Connector")
                connection_successful = True
                
            except ImportError:
                logger.warning("Cloud SQL Python Connector not available")
            except Exception as e:
                logger.warning(f"Cloud SQL Python Connector failed: {e}")
        
        # Approach 3: Fallback to simpler connection string
        if not connection_successful:
            try:
                # Try a simpler connection format
                fallback_url = settings.DATABASE_URL.replace(
                    "?host=/cloudsql/project-0990a5d7-310c-4a56-837:asia-south1:ods-database", 
                    ""
                )
                if fallback_url != settings.DATABASE_URL:
                    # This means we had a Cloud SQL URL, try without the socket
                    logger.warning("Trying fallback connection without Unix socket")
                    engine = create_engine(
                        fallback_url,
                        pool_size=settings.DATABASE_POOL_SIZE,
                        max_overflow=settings.DATABASE_MAX_OVERFLOW,
                        echo=settings.DEBUG,
                        pool_pre_ping=True
                    )
                    with engine.connect() as conn:
                        conn.execute("SELECT 1")
                    logger.info("Database engine created with fallback connection")
                    connection_successful = True
            except Exception as e:
                logger.error(f"Fallback connection also failed: {e}")
        
        if not connection_successful:
            raise Exception("All database connection approaches failed")
            
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    # For debugging purposes, let's still create an engine that will show the error
    engine = create_engine(
        settings.DATABASE_URL,
        echo=True
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

