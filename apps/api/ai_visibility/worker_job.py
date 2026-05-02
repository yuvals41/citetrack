# pyright: reportMissingImports=false, reportMissingTypeArgument=false

"""
RabbitMQ worker for AI Visibility scan jobs.

Consumes messages from 'scan.ai_visibility' topic, calls the stateless
scan executor, and updates job status in Redis.

NO database imports. NO Prisma. NO repositories.
"""

import os
import uuid
from typing import Optional

from loguru import logger
from solaraai_job_sdk.stores.redis import RedisStatusStore
from solaraai_job_sdk.types import BaseJobResult, JobState, JobStatus
from solaraai_messaging import PikaApp

from .scan_executor import execute_scan
from .schema import ScanInput, ScanProgress

pika_app = PikaApp.get_instance()
redis_store = RedisStatusStore(redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379"))


@pika_app.topic("scan.ai_visibility")
async def handle_scan(
    payload: ScanInput,
    *,
    correlation_id: Optional[str] = None,
    pattern: Optional[str] = None,
) -> dict:
    """Handle an AI Visibility scan job from RabbitMQ."""
    job_id = payload.job_id or correlation_id or str(uuid.uuid4())
    cid = correlation_id or job_id
    logger.info(
        f"[worker/{cid}] Received scan job: brand={payload.brand_name} "
        f"domain={payload.domain} providers={payload.providers}"
    )

    # Set status to RUNNING
    await redis_store.set_status(job_id, JobStatus(job_id=job_id, state=JobState.RUNNING))

    try:
        # Progress callback
        def on_progress(progress: ScanProgress) -> None:
            _emit_progress(cid, progress)

        # Execute the scan (stateless, no DB)
        output = await execute_scan(payload, on_progress=on_progress)

        # Set status to COMPLETED
        artifacts = {
            "mentions_count": len(output.mentions),
            "visibility_score": output.metrics.visibility_score,
            "citation_coverage": output.metrics.citation_coverage,
            "total_prompts": output.metrics.total_prompts,
            "total_mentioned": output.metrics.total_mentioned,
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
                        "duration": output.duration,
                    }
                ),
            ),
        )

        logger.info(
            f"[worker/{cid}] Done. mentions={len(output.mentions)} "
            f"visibility={output.metrics.visibility_score:.2%} "
            f"duration={output.duration:.1f}s"
        )
        return {
            "job_id": job_id,
            "status": "success",
            "mentions_count": len(output.mentions),
            "visibility_score": output.metrics.visibility_score,
            "duration": output.duration,
        }

    except Exception as exc:
        logger.error(f"[worker/{cid}] Job failed: {exc}", exc_info=True)
        await redis_store.set_status(
            job_id,
            JobStatus(
                job_id=job_id,
                state=JobState.FAILED,
                result=BaseJobResult.model_validate({"jobId": job_id, "status": "failed", "error": str(exc)}),
            ),
        )
        raise


def _emit_progress(cid: str, progress: ScanProgress) -> None:
    """Log progress events. In future, could publish to Redis pub/sub."""
    logger.info(
        f"[worker/{cid}] Progress: stage={progress.stage} "
        f"provider={progress.provider or '-'} "
        f"{progress.prompts_completed}/{progress.prompts_total} "
        f"msg={progress.message or '-'}"
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(pika_app.run())
