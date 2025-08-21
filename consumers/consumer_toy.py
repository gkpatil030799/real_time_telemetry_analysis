import json, os, collections
from confluent_kafka import Consumer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = os.getenv("TOPIC", "telemetry.power")
GROUP = os.getenv("GROUP", "toy-consumer")

c = Consumer({
    "bootstrap.servers": BOOTSTRAP,
    "group.id": GROUP,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True,
})
c.subscribe([TOPIC])

counts = collections.Counter()
print("Consuming… Ctrl+C to stop.")
try:
    while True:
        msg = c.poll(1.0)
        if msg is None: 
            continue
        if msg.error():
            print("Consumer error:", msg.error())
            continue
        key = msg.key().decode() if msg.key() else None
        data = json.loads(msg.value())
        counts[msg.partition()] += 1
        print(f"← key={key} part={msg.partition()} off={msg.offset()} watts={data['watts']}")
except KeyboardInterrupt:
    pass
finally:
    print("Counts by partition:", dict(counts))
    c.close()
