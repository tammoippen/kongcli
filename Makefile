KONG_VERSION=$(KONG_VERSION:0.13.1)


format:
	find src -type f -name "*.py" | xargs black
	find tests -type f -name "*.py" | xargs black

kong-db:
	docker run -it --rm -d --name kong-database \
		-p 5432:5432 \
		-e POSTGRES_USER=kong \
		-e POSTGRES_DB=kong \
		postgres:9.6

kong-setup:
	docker run -it --rm --name kong-startup \
		-e KONG_DATABASE=postgres \
		-e KONG_PG_HOST=kong-database \
		--link kong-database \
		kong:$(KONG_VERSION) kong migrations up

kong: kong-setup
	docker run -it --rm -d --name kong \
		-e KONG_DATABASE=postgres \
		-e KONG_PG_HOST=kong-database \
		-e KONG_CASSANDRA_CONTACT_POINTS=kong-database \
		-e KONG_PROXY_ACCESS_LOG=/dev/stdout \
		-e KONG_ADMIN_ACCESS_LOG=/dev/stdout \
		-e KONG_PROXY_ERROR_LOG=/dev/stderr \
		-e KONG_ADMIN_ERROR_LOG=/dev/stderr \
		-e KONG_ADMIN_LISTEN="0.0.0.0:8001, 0.0.0.0:8444 ssl" \
		-p 8001:8001 -p 8444:8444 \
		--link kong-database \
		kong:$(KONG_VERSION)
