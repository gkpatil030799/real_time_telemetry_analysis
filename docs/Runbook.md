# Runbook – Industrial Streaming (Phase 0)

## Start / Stop
- `make up`   → starts Kafka, Kafka UI, TimescaleDB, Grafana
- `make down` → stops all
- `make logs` → follow container logs
- `make clean`→ stop + remove volumes/networks

## Access (from Windows browser)
- Kafka UI: http://localhost:8080
- Grafana: http://localhost:3000  (admin / admin)
- TimescaleDB: localhost:5432 (user=postgres, pwd=postgres, db=energy)
- Kafka broker: localhost:9092

## Notes (WSL2)
- Open project: `code .`
- If Docker CLI fails in WSL, ensure Docker Desktop is running and WSL integration is enabled.

## Next (not today)
- Add producers under `/producers`
- Add Spark jobs under `/spark`
- Add SQL schemas under `/sql`
