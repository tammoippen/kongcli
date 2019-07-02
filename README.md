# kongcli

> TODO KONG tests 0.13, 0.14, 1.0, 1.1, 1.2

Used environment variables

- `KONG_BASE`: base url to the kong service
- `KONG_APIKEY`: API key for kong (if kong is behind a key auth)
- `KONG_BASIC_USER`: Basic Auth Username (if kong is behind basic auth)
- `KONG_BASIC_PASSWD`: Basic Auth Password (if kong is behind basic auth), if not set, you are prompted for the password.

Format: `fd '.*\.py' . | xargs black --target-version py36`
