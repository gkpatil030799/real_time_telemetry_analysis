# real_time_telemetry_analysis

## Phase 1 Quickstart
```bash
make up
make create-topic
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make producer   # terminal 1
make consumer   # terminal 2
make lag        # optional (see group lag)
