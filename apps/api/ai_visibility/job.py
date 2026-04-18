"""
K8s Job entry point for AI Visibility scan.

Reads JOB_PAYLOAD from env, calls scan executor directly,
updates Redis status, prints JSON result, exits.

No RabbitMQ. No worker.py import. No database. Simple.
"""

import asyncio
import json
import os
import sys
import time
import traceback
import uuid

from loguru import logger


async def main() -> None:
    start_time = time.time()

    # 1. Read payload from env
    raw = os.environ.get("JOB_PAYLOAD") or os.environ.get("JOB_DATA")
    if not raw:
        print(json.dumps({"status": "failed", "error": "No JOB_PAYLOAD environment variable set"}))
        sys.exit(1)

    try:
        payload_dict = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "failed", "error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    job_id = payload_dict.get("job_id") or os.environ.get("JOB_ID") or str(uuid.uuid4())
    correlation_id = payload_dict.get("correlation_id") or job_id

    logger.info(f"[job/{correlation_id}] Starting AI Visibility scan job: job_id={job_id}")

    # 2. Init services (no RabbitMQ, no DB!)
    from solaraai_job_sdk.stores.redis import RedisStatusStore
    from solaraai_job_sdk.types import BaseJobResult, JobState, JobStatus

    from ai_visibility.scan_executor import execute_scan
    from ai_visibility.schema import ScanInput, ScanProgress

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    redis_store = RedisStatusStore(redis_url=redis_url)

    # 3. Parse input
    try:
        scan_input = ScanInput(**payload_dict)
        scan_input.job_id = job_id
    except Exception as e:
        logger.error(f"[job/{correlation_id}] Invalid input: {e}")
        print(json.dumps({"status": "failed", "error": f"Invalid input: {e}"}))
        sys.exit(1)

    # 4. Set status to RUNNING
    await redis_store.set_status(job_id, JobStatus(job_id=job_id, state=JobState.RUNNING))

    try:
        # 5. Progress callback
        def on_progress(progress: ScanProgress) -> None:
            logger.info(
                f"[job/{correlation_id}] Progress: stage={progress.stage} "
                f"provider={progress.provider or '-'} "
                f"{progress.prompts_completed}/{progress.prompts_total}"
            )

        # 6. Call scan executor directly
        logger.info(
            f"[job/{correlation_id}] Calling executor: brand={scan_input.brand_name} providers={scan_input.providers}"
        )
        output = await execute_scan(scan_input, on_progress=on_progress)

        # 7. Set status to COMPLETED
        duration = time.time() - start_time
        artifacts = {
            "mentions_count": len(output.mentions),
            "visibility_score": output.metrics.visibility_score,
            "citation_coverage": output.metrics.citation_coverage,
            "avg_position": output.metrics.avg_position,
            "total_prompts": output.metrics.total_prompts,
            "total_mentioned": output.metrics.total_mentioned,
            "total_citations": output.metrics.total_citations,
            "provider_results": output.provider_results,
            "mentions": [m.model_dump() for m in output.mentions],
            "metrics": output.metrics.model_dump(),
        }

        await redis_store.set_status(
            job_id,
            JobStatus(
                job_id=job_id,
                state=JobState.COMPLETED,
                result=BaseJobResult.model_validate(
                    {
                        "jobId": job_id,
                        "status": "success",
                        "artifacts": artifacts,
                        "duration": duration,
                    }
                ),
            ),
        )

        logger.info(
            f"[job/{correlation_id}] Done in {duration:.1f}s. "
            f"mentions={len(output.mentions)} "
            f"visibility={output.metrics.visibility_score:.2%}"
        )
        print(
            json.dumps(
                {
                    "status": "success",
                    "job_id": job_id,
                    "mentions_count": len(output.mentions),
                    "visibility_score": output.metrics.visibility_score,
                    "duration": round(duration, 2),
                }
            )
        )
        sys.exit(0)

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"[job/{correlation_id}] Failed after {duration:.1f}s: {e}")
        traceback.print_exc()

        await redis_store.set_status(
            job_id,
            JobStatus(
                job_id=job_id,
                state=JobState.FAILED,
                result=BaseJobResult.model_validate(
                    {
                        "jobId": job_id,
                        "status": "failed",
                        "error": str(e),
                        "duration": duration,
                    }
                ),
            ),
        )

        print(json.dumps({"status": "failed", "error": str(e), "duration": round(duration, 2)}))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
