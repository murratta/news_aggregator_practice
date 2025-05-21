from fastapi.testclient import TestClient
from backend.app import app
from config import STUDENT_ID, SOURCES  # импортируешь список дефолтных источников

client = TestClient(app)

# 🔄 Хелперы
def clear_sources():
    res = client.delete(f"/sources/{STUDENT_ID}")
    assert res.status_code == 200

def restore_sources():
    for url in SOURCES:
        res = client.post(f"/sources/{STUDENT_ID}", json={"url": url})
        assert res.status_code == 200

# 🧪 Тест: пустой список
def test_get_empty_sources():
    clear_sources()
    res = client.get(f"/sources/{STUDENT_ID}")
    assert res.status_code == 200
    assert res.json() == {"sources": []}
    restore_sources()

# 🧪 Тест: добавление источника
def test_add_and_get_source():
    clear_sources()
    res1 = client.post(f"/sources/{STUDENT_ID}", json={"url": "https://example.com/rss"})
    assert res1.status_code == 200
    assert "https://example.com/rss" in res1.json()["sources"]

    res2 = client.get(f"/sources/{STUDENT_ID}")
    assert res2.json()["sources"] == ["https://example.com/rss"]
    restore_sources()
