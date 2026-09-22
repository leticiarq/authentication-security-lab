#!/usr/bin/env bash
set -euo pipefail

release_project="${VAULTA_RELEASE_PROJECT:-vaulta-release-check}"
release_web_port="${VAULTA_RELEASE_WEB_PORT:-18001}"
release_db_port="${VAULTA_RELEASE_DB_PORT:-55432}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export WEB_PORT="${release_web_port}"
export POSTGRES_PORT_FORWARD="${release_db_port}"

compose=(docker compose --project-directory "${repo_root}" -p "${release_project}")

cleanup() {
    "${compose[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

cd "${repo_root}"

echo "[1/6] Validating Compose configuration"
"${compose[@]}" config --quiet

echo "[2/6] Building the pinned application image"
"${compose[@]}" build web

echo "[3/6] Running lint checks"
docker run --rm \
    -v "${repo_root}:/workspace" \
    -w /workspace \
    python:3.12-slim \
    sh -c "pip install --quiet ruff==0.12.12 && ruff check app tests"

echo "[4/6] Running Django checks and migration drift detection"
"${compose[@]}" run --rm web python manage.py check
"${compose[@]}" run --rm web python manage.py makemigrations --check --dry-run

echo "[5/6] Running the full suite against temporary PostgreSQL"
"${compose[@]}" run --rm web \
    python manage.py test ../tests --settings=config.settings.test_postgres

echo "[6/6] Starting, seeding and probing the clean application"
"${compose[@]}" up --detach web
curl --fail --silent --show-error \
    --retry 30 \
    --retry-delay 1 \
    --retry-connrefused \
    --retry-all-errors \
    "http://127.0.0.1:${release_web_port}/health/" >/dev/null
"${compose[@]}" exec -T web python manage.py seed_dev
curl --fail --silent --show-error \
    "http://127.0.0.1:${release_web_port}/health/" >/dev/null

echo "Release checks passed. Temporary containers and volumes will be removed."
