"""
Phase 9 soak test — drives a realistic mixed-mode workload through the
ResourceScheduler and logs VRAM/RAM usage over time.

Purpose: manually verify the Phase 9 acceptance criterion that "measured
VRAM usage stays within the profile's budget under a realistic mixed-mode
usage scenario". Real GPU measurement isn't practical in ordinary CI, so
this is a documented manual/periodic script.

Usage (from apps/api, with the venv active and Ollama running):

    python ../scripts/soak_test_scheduler.py --seconds 120 --profile BALANCED

The script acquires each model in a realistic pattern (talk -> vision ->
talk -> stt), emits a periodic resource snapshot, and finishes by reporting
the peak VRAM/RAM used and whether it stayed within budget.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.core.resource_scheduler import build_default_scheduler  # noqa: E402


async def run(seconds: int, profile: str) -> None:
    scheduler = build_default_scheduler()
    await scheduler.set_profile(profile)
    print(f"Soak test starting — profile={profile}, duration={seconds}s")
    print("models:", ", ".join(mid for mid, _ in scheduler.registry.list()))

    peak_vram = 0.0
    peak_ram = 0
    start = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start < seconds:
        snap = await scheduler.snapshot()
        used = snap["vram_used_mb"] or 0
        peak_vram = max(peak_vram, used)
        peak_ram = max(peak_ram, snap["ram_used_mb"])
        loaded = [m["model_id"] for m in snap["models"] if m["loaded"]]
        print(
            f"  t={asyncio.get_event_loop().time() - start:5.0f}s "
            f"vram={used:6.0f}/{snap['vram_budget_mb']:5d} MB "
            f"ram={snap['ram_used_mb']:5d} MB loaded={loaded}"
        )

        async with scheduler.acquire("llm"):
            async for _ in scheduler.registry.get("llm")[1].generate_stream(
                "Summarize the soak test in one line."
            ):
                pass
        await asyncio.sleep(1.0)

        async with scheduler.acquire("vision"):
            pass
        await asyncio.sleep(1.0)

        async with scheduler.acquire("stt"):
            pass

        await asyncio.sleep(2.0)

    budget = scheduler.profile_config.vram_budget_mb
    within = peak_vram <= budget
    print(f"Peak VRAM used: {peak_vram:.0f} MB / budget {budget} MB -> "
          f"{'WITHIN BUDGET' if within else 'OVER BUDGET'}")
    print(f"Peak RAM used: {peak_ram} MB / budget {scheduler.profile_config.ram_budget_mb} MB")
    sys.exit(0 if within else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 9 scheduler soak test")
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--profile", default="BALANCED",
                        choices=["ECO", "BALANCED", "PERFORMANCE"])
    args = parser.parse_args()
    asyncio.run(run(args.seconds, args.profile))


if __name__ == "__main__":
    main()
