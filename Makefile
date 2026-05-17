.PHONY: dev-backend dev-frontend format lint install

export PATH := $(PWD)/.local_node/bin:$(PATH)

dev-backend:
	uv run uvicorn src.main:app --reload

dev-frontend:
	cd frontend && npm run dev

format:
	uv run ruff format .
	uv run ruff check --fix .

install:
	uv sync
	cd frontend && npm install
