"""CLI for the MLOps pipeline.  Run from the ml/ directory:

    python cli.py train         # run full training pipeline (retrain + promote)
    python cli.py list          # registry overview (versions + champions)
    python cli.py history       # recent experiment runs
    python cli.py card <task>   # print the champion model card for a task

On Catalyst this CLI is the unit invoked by a Cron job for scheduled retraining.
"""
from __future__ import annotations

import json
import os
import sys

# Windows consoles default to cp1252 and choke on unicode (→ · ±) in logs.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def main(argv=None):
    argv = argv or sys.argv[1:]
    cmd = argv[0] if argv else "train"

    if cmd == "train":
        import pipeline
        pipeline.run()

    elif cmd in ("list", "registry"):
        import registry
        info = registry.list_models()
        for task, d in info.items():
            champ = d["champion"]
            cv = f"v{champ['version']}" if champ else "—"
            print(f"{task:18s} versions={d['versions']}  champion={cv}"
                  + (f"  {champ['primary_metric']}={champ['metrics'].get(champ['primary_metric'])}"
                     if champ else ""))

    elif cmd == "history":
        import tracking
        for r in tracking.read_history(30):
            m = r.get("metrics", {})
            key = next((k for k in ("roc_auc", "mae", "flagged_pct") if k in m), None)
            fam = r.get("family", "") or ""
            val = m.get(key) if key else ""
            print(f"{r.get('logged_at','')[:19]}  {r.get('task','?'):16s} {fam:14s} "
                  f"{key}={val}  promoted={r.get('promotion',{}).get('promoted')}")

    elif cmd == "card":
        import config
        task = argv[1]
        champ_path = os.path.join(config.REGISTRY_DIR, task, "champion.json")
        if not os.path.exists(champ_path):
            print("no champion for", task); return
        v = json.load(open(champ_path))["version"]
        card = os.path.join(config.REGISTRY_DIR, task, f"v{v}", "model_card.md")
        print(open(card, encoding="utf-8").read())

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
