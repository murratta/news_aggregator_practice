![CI](https://github.com/<User>/<Repo>/actions/workflows/ci.yml/badge.svg)
docker run -d -p 8000:8000 ghcr.io/<User>/news-backend:latest
sleep 5
curl http://localhost:8000/info
docker stop $(docker ps -q --filter ancestor=ghcr.io/<User>/news-backend:latest)
