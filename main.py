"""
Application entrypoint.

WHY FASTAPI: async-native, Pydantic-based validation out of the box,
and auto-generated OpenAPI/Swagger docs at /docs — critical for a
project you'll demo, since the API is self-documenting.

Routers are registered here with tags; each tag becomes a labeled
section in Swagger (Products, Orders, Analytics, ...). As we build
Phase 4 onward, each new router module gets one line added here —
main.py itself never grows business logic.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, auth, products, distributors, retailers, inventory, sales, orders, excel_import, dashboard, troubleshooting

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise FMCG Distribution & Analytics Platform API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(distributors.router, prefix="/api")
app.include_router(retailers.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(sales.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(excel_import.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(troubleshooting.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "BizSync API is running", "docs": "/docs"}
