from fastapi import FastAPI

from security_daily.api.quiz_router import router as quiz_router
from security_daily.api.news_router import router as news_router

app = FastAPI(title="Security Daily API")
app.include_router(quiz_router)
app.include_router(news_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
