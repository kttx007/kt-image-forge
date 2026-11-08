"""Minimal LOOP CLI: plan / bundle / status."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bundle import build_manual_web_bundle
from .engine import create_run, prepare_slot, run_status
from .planner import plan_job


def _read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="kt-loop")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--job", required=True)
    p_plan.add_argument("--out", required=True)

    p_bundle = sub.add_parser("bundle")
    p_bundle.add_argument("--job", required=True)
    p_bundle.add_argument("--slot", required=True)
    p_bundle.add_argument("--out", required=True)

    p_status = sub.add_parser("status")
    p_status.add_argument("--run", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "plan":
        job = _read_json(args.job)
        out = Path(args.out)
        payload = {"plan": plan_job(job), "run": create_run(job)}
        _write(out, payload)
        print(out)
        return 0

    if args.cmd == "bundle":
        job = _read_json(args.job)
        run = create_run(job)
        prepare_slot(job, run, args.slot)
        bundle = build_manual_web_bundle(job, args.slot)
        out = Path(args.out)
        _write(out / "PROMPT.md", bundle["prompt"])
        _write(out / "FACTS.json", bundle["facts"])
        _write(out / "REFERENCES.json", bundle["references"])
        _write(out / "RETURN_INSTRUCTIONS.md", bundle["return_instructions"])
        _write(out / "run.json", run)
        print(out)
        return 0

    if args.cmd == "status":
        run = _read_json(args.run)
        print(json.dumps(run_status(run), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
