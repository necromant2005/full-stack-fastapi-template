from fastapi import APIRouter, Depends
from sqlmodel import func, select

from app.api.deps import SessionDep, require_permission
from app.models import MetricsInsights, Permission, User

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "/insights",
    dependencies=[Depends(require_permission(Permission.metrics_view))],
    response_model=MetricsInsights,
)
def read_metrics_insights(session: SessionDep) -> MetricsInsights:
    total_users = session.exec(select(func.count()).select_from(User)).one()
    active_users = session.exec(
        select(func.count()).select_from(User).where(User.is_active)
    ).one()
    return MetricsInsights(total_users=total_users, active_users=active_users)
