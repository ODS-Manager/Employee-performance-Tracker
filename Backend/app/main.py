from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.middleware import CSRFMiddleware, SecurityHeadersMiddleware
from app.core.db_migrations import ensure_orders_file_product_team_index_non_unique
from app.api.v1 import auth, users, teams, orders, dashboard, billing, organizations, database, reference, metrics, productivity, quality_audits, examiner_weekly_targets, team_user_aliases, attendance, fa_names
from app.tasks.session_cleanup import start_session_cleanup_scheduler

# Scheduler instance
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    global scheduler
    ensure_orders_file_product_team_index_non_unique()
    scheduler = start_session_cleanup_scheduler()
    scheduler.start()
    yield
    # Shutdown
    if scheduler:
        scheduler.shutdown()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Order & Performance Management System API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Security Headers Middleware (applied first)
app.add_middleware(SecurityHeadersMiddleware)

# CSRF Protection Middleware - TEMPORARILY DISABLED FOR DEBUGGING
# TODO: Re-enable after fixing cross-origin cookie issues
# app.add_middleware(CSRFMiddleware)

# CORS middleware (applied last, runs first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ods-frontend-302004244593.asia-south1.run.app", "http://localhost:3000"],
    allow_credentials=True,  # Important: required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"],  # Expose cookies to frontend
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(teams.router, prefix="/api/v1/teams", tags=["Teams"])
app.include_router(team_user_aliases.router, prefix="/api/v1", tags=["Team User Aliases"])
app.include_router(fa_names.router, prefix="/api/v1/fa-names", tags=["FA Names"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(reference.router, prefix="/api/v1/reference", tags=["Reference Data"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Performance Metrics"])
app.include_router(productivity.router, prefix="/api/v1/productivity", tags=["Productivity"])
app.include_router(quality_audits.router, prefix="/api/v1", tags=["Quality Audits"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
app.include_router(database.router, prefix="/api/v1/database", tags=["Database"])
app.include_router(examiner_weekly_targets.router, prefix="/api/v1/weekly-targets", tags=["Weekly Targets"])
app.include_router(attendance.router, prefix="/api/v1", tags=["Attendance"])

@app.get("/")
async def root():
    return {
        "message": "ODS Backend API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
