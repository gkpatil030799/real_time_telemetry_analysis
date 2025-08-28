# spark/stream_power_to_bronze.py
# Phase 2: Kafka -> Spark Structured Streaming -> TimescaleDB (bronze.raw_power)

import os
import json
from datetime import datetime
from dotenv import load_dotenv

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, lit, concat_ws, sha2, regexp_replace, to_timestamp, coalesce
)
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

import psycopg2
from psycopg2.extras import execute_values, Json

# =========================
# Env
# =========================
load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC           = os.getenv("TOPIC", "telemetry.power")

PG_HOST     = os.getenv("PG_HOST", "localhost")
PG_PORT     = int(os.getenv("PG_PORT", "5432"))
PG_DB       = os.getenv("PG_DB", "energy")
PG_USER     = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")

CHECKPOINT  = os.getenv("SPARK_CHECKPOINT", "./checkpoints/power_bronze")
TARGET      = "bronze.raw_power"

# =========================
# SparkSession
# (uses Maven coordinates; great for portability & resumes)
# =========================
spark = (
    SparkSession.builder
    .appName("factory-power-bronze")
    .config(
        "spark.jars.packages",
        # Match pyspark==3.5.1 (Scala 2.12). Postgres JDBC for convenience.
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,"
        "org.postgresql:postgresql:42.7.3"
    )
    .config("spark.ui.showConsoleProgress", "true")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# =========================
# Incoming payload schema (from your producer)
# =========================
# {
#   "ts": "...Z",
#   "machine_id": "M001",
#   "phase": "A|B|C",
#   "watts": 400-1200,
#   "volts": 200-250,
#   "amps":  1-8
# }
payload_schema = StructType([
    StructField("ts",         StringType(), True),
    StructField("machine_id", StringType(), True),
    StructField("phase",      StringType(), True),
    StructField("watts",      DoubleType(), True),
    StructField("volts",      DoubleType(), True),
    StructField("amps",       DoubleType(), True),
])

# =========================
# Kafka source
# =========================
raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "latest")
    .load()
)

json_df = raw.selectExpr("CAST(value AS STRING) AS json_str")

# =========================
# Parse + map to bronze schema
# =========================
parsed = (
    json_df
    .select(
        from_json(col("json_str"), payload_schema).alias("j"),
        col("json_str").alias("raw_payload")
    )
    # Remove trailing 'Z' to parse flexibly; try ms + no-ms formats.
    .withColumn("ts_clean", regexp_replace(col("j.ts"), "Z$", ""))
    .withColumn("event_ts_ms", to_timestamp(col("ts_clean"), "yyyy-MM-dd'T'HH:mm:ss.SSS"))
    .withColumn("event_ts_s",  to_timestamp(col("ts_clean"), "yyyy-MM-dd'T'HH:mm:ss"))
    .select(
        # Deterministic id (prevents duplicates on retries/restarts)
        sha2(concat_ws("|", col("j.machine_id"), col("j.ts")), 256).alias("event_id"),
        coalesce(col("event_ts_ms"), col("event_ts_s")).alias("event_ts"),
        col("j.machine_id").alias("machine_id"),
        (col("j.watts") / 1000.0).alias("power_kw"),  # watts -> kW
        col("j.volts").alias("voltage_v"),
        col("j.amps").alias("current_a"),
        lit(None).cast("double").alias("temp_c"),     # not produced yet
        col("raw_payload")
    )
)

# =========================
# Postgres writer (idempotent upsert)
# raw_power PK: (event_id, event_ts)
# =========================
UPSERT_SQL = f"""
INSERT INTO {TARGET}
(event_id, event_ts, machine_id, power_kw, voltage_v, current_a, temp_c, ingest_ts, raw_payload)
VALUES %s
ON CONFLICT (event_id, event_ts) DO NOTHING;
"""

def write_batch_to_pg(rows):
    if not rows:
        return
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )
    try:
        with conn, conn.cursor() as cur:
            execute_values(cur, UPSERT_SQL, rows, page_size=5000)
    finally:
        conn.close()

def foreach_batch(df, epoch_id):
    # Phase-2 scale: collect() is acceptable; we’ll optimize later.
    now = datetime.utcnow()
    batch = []
    for r in df.collect():
        # Proper jsonb insert of the original payload
        raw_obj = None
        if r["raw_payload"]:
            try:
                raw_obj = json.loads(r["raw_payload"])
            except Exception:
                raw_obj = None
        batch.append((
            r["event_id"],
            r["event_ts"],
            r["machine_id"],
            r["power_kw"],
            r["voltage_v"],
            r["current_a"],
            r["temp_c"],
            now,
            Json(raw_obj),
        ))
    write_batch_to_pg(batch)

# =========================
# Start the stream
# =========================
query = (
    parsed.writeStream
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT)
    .foreachBatch(foreach_batch)
    .start()
)

query.awaitTermination()
