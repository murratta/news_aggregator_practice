from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import config
from config import STUDENT_ID, SOURCES
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# Пам'ять для джерел
store = {STUDENT_ID: SOURCES.copy()}

# Пам’ять для новин
news_store = {STUDENT_ID: []}

# Аналізатор тональності
analyzer = SentimentIntensityAnalyzer()

origins = [
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    # можно добавить сюда и другие адреса, с которых разрешаешь запросы
]
@asynccontextmanager
async def lifespan(app: FastAPI):
    student_id = getattr(config, "STUDENT_ID", None)
    sources = getattr(config, "SOURCES", [])
    if student_id and isinstance(sources, list):
        store[student_id] = list(sources)
        print(f"[startup] loaded {len(sources)} feeds for {student_id}")
    yield
    # Здесь можно добавить код для shutdown, если нужно

# Создание приложения
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
fake_users_db = {
    STUDENT_ID: {
        "username": STUDENT_ID,
        "full_name": STUDENT_ID,
        "hashed_password": "password123",  # нерекомендовано зберігати так на проді
        "disabled": False,
    }
}

analyzer = SentimentIntensityAnalyzer()
news_store = {STUDENT_ID: []}
# Пам'ять для збереження джерел (для кожного STUDENT_ID окремо)
store = {STUDENT_ID: SOURCES.copy()}

@app.get("/sources/{student_id}")
def get_sources(student_id: str):
    if student_id not in store:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"sources": store[student_id]}


@app.post("/sources/{student_id}")
def add_source(student_id: str, source: dict = Body(...)):
    url = source.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")

    if student_id != STUDENT_ID:
        raise HTTPException(status_code=404, detail="Student not found")

    if student_id not in news_store:
        news_store[student_id] = []

    store.setdefault(student_id, []).append(url)
    return {"sources": store[student_id]}


@app.post("/fetch/{student_id}")
async def fetch_feed(student_id: str):
    if student_id not in store:
        raise HTTPException(status_code=404, detail="Not Found")

    news_store[student_id].clear()
    fetched = 0

    for url in store[student_id]:
        try:
            feed = feedparser.parse(url, request_headers={'User-Agent': 'Mozilla/5.0'})
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue

        if not hasattr(feed, "entries"):
            print(f"No entries found for {url}")
            continue

        for entry in feed.entries:
            news_store[student_id].append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", "")
            })
            fetched += 1

    return {"fetched": fetched}

@app.post("/sources/{student_id}")
def add_source(student_id: str, payload: dict):
    if student_id != STUDENT_ID:
        raise HTTPException(status_code=404, detail="Student not found")
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    store[student_id].append(url)
    return {"sources": store[student_id]}

@app.post("/fetch/{student_id}")
def fetch_news(student_id: str):
    if student_id != STUDENT_ID:
        raise HTTPException(status_code=404, detail="Student not found")
    # Очищаємо попередній кеш
    news_store[student_id].clear()
    fetched = 0
    for url in config.SOURCES:
        feed = feedparser.parse(url)
        for entry in getattr(feed, "entries", []):
            news_store[student_id].append({
                "title": entry.get("title", ""),
                "link":  entry.get("link", ""),
                "published": entry.get("published", "")
            })
            fetched += 1
    return {"fetched": fetched}

@app.get("/news/{student_id}")
def get_news(student_id: str):
    if student_id not in news_store:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"articles": news_store[student_id]}


@app.post("/analyze/{student_id}")
def analyze_tone(student_id: str):
    if student_id != STUDENT_ID:
        raise HTTPException(status_code=404, detail="Student not found")
    articles = news_store.get(student_id, [])
    result = []
    for art in articles:
        text = art.get("title", "")
        scores = analyzer.polarity_scores(text)
        comp = scores["compound"]
        if comp >= 0.05:
            label = "positive"
        elif comp <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        result.append({**art, "sentiment": label, "scores": scores})

        # Додаємо поля "sentiment" і "scores" в копію статті
        result.append({**art, "sentiment": label, "scores": scores})
    return {"analyzed": len(result), "articles": result}
