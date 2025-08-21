# Runbook – Industrial Streaming (Phase 0)

## Start / Stop
- `make up`   → starts Kafka, Kafka UI, TimescaleDB, Grafana
- `make down` → stops all
- `make logs` → follow container logs
- `make clean`→ stop + remove volumes/networks

## Access (from Windows browser)
- Kafka UI: http://localhost:8081
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

# Runbook – Industrial Streaming (Phase 1)

## Kafka Topic Management
- `make create-topic`   → create telemetry topic (default 3 partitions)
- `make list-topics`    → list topics
- `make describe-topic` → show partition/replica layout
- `make alter-6`        → scale telemetry topic to 6 partitions
- `make lag`            → view consumer group lag
- `make reset`          → reset offsets to earliest for toy-consumer group

## Producer / Consumer
- `make venv`     → create virtual environment + install requirements
- `make producer` → start `producer_power.py` (~5 events/sec, keyed by `machine_id`)
- `make consumer` → start `consumer_toy.py`, prints key/partition/offset and counts

### Expected Behavior
- **Producer** prints delivery reports like: key=M001 part=2 off=42
- **Consumer** prints consumed events and ends with: Counts by partition: {0: 100, 1: 95, 2: 105}
- **Kafka UI** (http://localhost:8081) shows:
- Topic: `telemetry.power`
- Partitions: 3
- Offsets growing while producer runs

## Verification Steps
1. Run `make up` and `make create-topic`.
2. Start producer (`make producer`) and consumer (`make consumer`) in separate terminals.
3. Check partition offsets and lag via:
 - Kafka UI (Topics → telemetry.power)
 - `make lag` CLI
4. Scale partitions to 6 with `make alter-6`, observe redistribution in consumer output.
5. Interview nugget:  
 *“We keyed messages by machine_id to guarantee per-device ordering, while scaling horizontally across partitions. We also monitored partition skew and demonstrated why keys matter.”*

## Notes
- Add `.venv/` to `.gitignore` so local virtual env isn’t committed.
- Use `make clean` if you want to reset all containers/volumes and start fresh.


