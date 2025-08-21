import json, random, time, os
from datetime import datetime
from confluent_kafka import Producer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = os.getenv("TOPIC", "telemetry.power")
p = Producer({"bootstrap.servers": BOOTSTRAP})

MACHINES = [f"M{str(i).zfill(3)}" for i in range(1, 21)]

def delivery_report(err, msg):
    if err: print("Delivery failed:", err)
    else:   print(f"✓ key={msg.key().decode()} part={msg.partition()} off={msg.offset()}")

def random_event(mid):
    return {
        "ts": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "machine_id": mid,
        "phase": random.choice(["A","B","C"]),
        "watts": round(random.uniform(400.0, 1200.0), 2),
        "volts": round(random.uniform(200.0, 250.0), 1),
        "amps": round(random.uniform(1.0, 8.0), 2),
    }

def main(rate=5):
    interval = 1.0 / rate
    print(f"Producing to {TOPIC} @ ~{rate}/s. Ctrl+C to stop.")
    try:
        while True:
            mid = random.choices(MACHINES, weights=[5 if m in ("M001","M002","M003") else 1 for m in MACHINES])[0]
            p.produce(TOPIC, key=mid.encode(), value=json.dumps(random_event(mid)).encode(), on_delivery=delivery_report)
            p.poll(0)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        p.flush()

if __name__ == "__main__":
    main(rate=float(os.getenv("RATE", "5")))
