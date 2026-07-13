"""sortarr.api.routes.metrics — Prometheus metrics endpoint."""

from fastapi import APIRouter, Response

from sortarr.metrics import get_metrics_text

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def metrics() -> Response:
    """Return Prometheus metrics in text format."""
    return Response(
        content=get_metrics_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
