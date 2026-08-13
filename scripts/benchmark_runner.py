"""
Spectra Phase 10 Expanded Benchmark Runner.

Measures:
  - Health endpoint latency (p50, p95, p99 over N requests)
  - WebSocket handshake latency
  - Cold vs Warm start latency for inference / task acquisition
  - First-token latency & tokens/second throughput
  - CPU, system RAM, and GPU VRAM resource usage
  - ResourceScheduler activity (loaded models, profile, load/unload state)

Usage:
  python scripts/benchmark_runner.py --base-url http://127.0.0.1:8000 --profile BALANCED --output benchmarks/report.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx

try:
    import psutil
except ImportError:
    psutil = None

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))


async def measure_health_latency(base_url: str, requests_count: int = 50) -> Dict[str, float]:
    latencies: List[float] = []
    async with httpx.AsyncClient() as client:
        for _ in range(requests_count):
            start = time.perf_counter()
            resp = await client.get(f"{base_url}/health", timeout=5.0)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            if resp.status_code == 200:
                latencies.append(elapsed_ms)
            await asyncio.sleep(0.01)

    if not latencies:
        return {"p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "avg_ms": 0.0}

    latencies.sort()
    n = len(latencies)
    return {
        "p50_ms": round(latencies[int(n * 0.50)], 2),
        "p95_ms": round(latencies[int(n * 0.95)], 2),
        "p99_ms": round(latencies[min(int(n * 0.99), n - 1)], 2),
        "avg_ms": round(sum(latencies) / n, 2),
        "total_requests": n,
    }


async def measure_ws_handshake(ws_url: str, trials: int = 5) -> Dict[str, float]:
    import websockets

    latencies: List[float] = []
    for _ in range(trials):
        start = time.perf_counter()
        try:
            async with websockets.connect(ws_url) as ws:
                _ = await ws.recv()  # connection_status
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                latencies.append(elapsed_ms)
        except Exception:
            pass
        await asyncio.sleep(0.1)

    if not latencies:
        return {"avg_handshake_ms": 0.0}

    return {"avg_handshake_ms": round(sum(latencies) / len(latencies), 2), "trials": len(latencies)}


async def measure_llm_streaming(ws_url: str, prompt: str = "Count from 1 to 5 clearly.") -> Dict[str, Any]:
    import websockets

    metrics: Dict[str, Any] = {
        "cold_start_first_token_ms": 0.0,
        "warm_start_first_token_ms": 0.0,
        "tokens_per_second": 0.0,
        "total_tokens": 0,
    }

    async def _run_prompt(ws, is_cold: bool) -> tuple[float, int, float]:
        req = {
            "type": "task.request",
            "timestamp": str(time.time()),
            "payload": {"text": prompt, "mode": "talk"},
        }
        start = time.perf_counter()
        await ws.send(json.dumps(req))

        first_token_time = None
        token_count = 0

        while True:
            try:
                msg_raw = await asyncio.wait_for(ws.recv(), timeout=15.0)
                msg = json.loads(msg_raw)
                msg_type = msg.get("type")
                if msg_type == "llm.token":
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
                    token_count += 1
                elif msg_type in ("task.completed", "task.failed"):
                    break
            except asyncio.TimeoutError:
                break

        end = time.perf_counter()
        first_token_ms = ((first_token_time or end) - start) * 1000.0
        duration_s = max(end - (first_token_time or start), 0.001)
        tps = token_count / duration_s if token_count > 0 else 0.0

        return first_token_ms, token_count, tps

    try:
        async with websockets.connect(ws_url) as ws:
            _ = await ws.recv()  # connection_status
            _ = await ws.recv()  # orb.state_changed

            cold_first_token_ms, cold_tokens, _ = await _run_prompt(ws, is_cold=True)
            metrics["cold_start_first_token_ms"] = round(cold_first_token_ms, 2)

            await asyncio.sleep(0.5)

            warm_first_token_ms, warm_tokens, warm_tps = await _run_prompt(ws, is_cold=False)
            metrics["warm_start_first_token_ms"] = round(warm_first_token_ms, 2)
            metrics["total_tokens"] = cold_tokens + warm_tokens
            metrics["tokens_per_second"] = round(warm_tps, 2)
    except Exception as e:
        metrics["error"] = str(e)

    return metrics


async def capture_system_resources() -> Dict[str, Any]:
    from app.core.resource_monitor import build_resource_monitor
    from app.core.resource_scheduler import build_default_scheduler

    cpu_percent = psutil.cpu_percent(interval=0.1) if psutil else 0.0
    memory_info = psutil.virtual_memory() if psutil else None
    ram_used_mb = round(memory_info.used / (1024 * 1024), 2) if memory_info else 0.0

    monitor = build_resource_monitor()
    snap = await monitor.snapshot()

    scheduler = build_default_scheduler(monitor=monitor)
    snap_sched = await scheduler.snapshot()

    return {
        "cpu_percent": cpu_percent,
        "ram_used_mb": ram_used_mb,
        "vram_used_mb": snap.vram_used_mb or snap_sched.get("vram_used_mb", 0.0),
        "vram_budget_mb": snap_sched.get("vram_budget_mb", 4096),
        "power_profile": snap_sched.get("profile", "BALANCED"),
        "scheduler_activity": {
            "models": snap_sched.get("models", []),
            "loaded_count": sum(1 for m in snap_sched.get("models", []) if m.get("loaded")),
        },
    }


async def run_benchmark_suite(base_url: str, ws_url: str, profile: str) -> Dict[str, Any]:
    print(f"Starting Spectra Benchmark Suite against {base_url} (profile={profile})...")

    health_res = await measure_health_latency(base_url)
    ws_res = await measure_ws_handshake(ws_url)
    llm_res = await measure_llm_streaming(ws_url)
    res_snap = await capture_system_resources()

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "profile": profile,
        "health_latency": health_res,
        "ws_handshake": ws_res,
        "llm_streaming": llm_res,
        "resources": res_snap,
    }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Spectra Phase 10 Benchmark Suite")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--ws-url", default="ws://127.0.0.1:8000/ws")
    parser.add_argument("--profile", default="BALANCED")
    parser.add_argument("--output", default="benchmarks/report.json")
    args = parser.parse_args()

    report = asyncio.run(run_benchmark_suite(args.base_url, args.ws_url, args.profile))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n--- BENCHMARK REPORT SUMMARY ---")
    print(f"Health p50: {report['health_latency']['p50_ms']} ms | p95: {report['health_latency']['p95_ms']} ms")
    print(f"WS Handshake: {report['ws_handshake']['avg_handshake_ms']} ms")
    print(f"LLM Cold Start First Token: {report['llm_streaming']['cold_start_first_token_ms']} ms")
    print(f"LLM Warm Start First Token: {report['llm_streaming']['warm_start_first_token_ms']} ms")
    print(f"LLM Throughput: {report['llm_streaming']['tokens_per_second']} tokens/sec")
    print(f"CPU: {report['resources']['cpu_percent']}% | RAM: {report['resources']['ram_used_mb']} MB | VRAM: {report['resources']['vram_used_mb']} MB")
    print(f"Report written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
