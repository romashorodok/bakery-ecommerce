
run:
	uvicorn bakery_ecommerce.app:app --port 9000 --reload

migrate:
	alembic upgrade head

db:
	docker exec -it bakery-ecommerce-postgres-1 psql -U admin postgres

test:
	poetry run pytest

stripe:
	stripe listen --forward-to localhost:9000/api/payments/stripe/webhook
