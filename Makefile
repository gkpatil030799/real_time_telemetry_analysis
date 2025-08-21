# Phase 0 infra controls
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v --remove-orphans
	docker system prune -f

# Phase 1 infra controls

BOOT := kafka:29092
TOPIC := telemetry.power
KT := /opt/bitnami/kafka/bin/kafka-topics.sh
KCG := /opt/bitnami/kafka/bin/kafka-consumer-groups.sh
HOST_BOOT := localhost:9092

create-topic:
	docker compose exec kafka bash -lc '$(KT) --bootstrap-server $(BOOT) --create --topic $(TOPIC) --partitions 3 --replication-factor 1'

list-topics:
	docker compose exec kafka bash -lc '$(KT) --bootstrap-server $(BOOT) --list'

describe-topic:
	docker compose exec kafka bash -lc '$(KT) --bootstrap-server $(BOOT) --describe --topic $(TOPIC)'

alter-6:
	docker compose exec kafka bash -lc '$(KT) --bootstrap-server $(BOOT) --alter --topic $(TOPIC) --partitions 6'

lag:
	docker compose exec kafka bash -lc '$(KCG) --bootstrap-server $(BOOT) --describe --group toy-consumer'

reset:
	docker compose exec kafka bash -lc '$(KCG) --bootstrap-server $(BOOT) --reset-offsets --to-earliest --group toy-consumer --topic $(TOPIC) --execute'

venv:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

producer:
	KAFKA_BOOTSTRAP=$(HOST_BOOT) TOPIC=$(TOPIC) RATE=5 .venv/bin/python producers/producer_power.py

consumer:
	KAFKA_BOOTSTRAP=$(HOST_BOOT) TOPIC=$(TOPIC) GROUP=toy-consumer .venv/bin/python producers/consumer_toy.py