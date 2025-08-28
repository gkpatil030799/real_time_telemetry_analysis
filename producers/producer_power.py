import json, random, time, os
from datetime import datetime
from confluent_kafka import Producer

# --- Environment ---
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC     = os.getenv("TOPIC", "telemetry.power")
RATE      = float(os.getenv("RATE", "5"))  # events per second

# --- Producer setup ---
p = Producer({"bootstrap.servers": BOOTSTRAP})

# Weighted machine distribution (M001–M003 are "hotter")
MACHINES = [f"M{str(i).zfill(3)}" for i in range(1, 21)]
WEIGHTS  = [5 if m in ("M001", "M002", "M003") else 1 for m in MACHINES]

def delivery_report(err, msg):
    """Callback for Kafka delivery confirmation."""
    if err is not None:
        print("Delivery failed:", err)
    else:
        print(f"key={msg.key().decode()} part={msg.partition()} off={msg.offset()}")

def random_event(machine_id: str) -> dict:
    """Generate one telemetry event."""
    return {
        "ts": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "machine_id": machine_id,
        "phase": random.choice(["A", "B", "C"]),
        "watts": round(random.uniform(400.0, 1200.0), 2),
        "volts": round(random.uniform(200.0, 250.0), 1),
        "amps": round(random.uniform(1.0, 8.0), 2),
    }

def main():
    interval = 1.0 / RATE
    print(f"Producing to {TOPIC} @ ~{RATE}/s. Ctrl+C to stop.")
    try:
        while True:
            mid = random.choices(MACHINES, weights=WEIGHTS)[0]
            event = random_event(mid)
            p.produce(
                TOPIC,
                key=mid.encode(),
                value=json.dumps(event).encode(),
                on_delivery=delivery_report,
            )
            p.poll(0)  # serve delivery callbacks
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        p.flush()

if __name__ == "__main__":
    main()
