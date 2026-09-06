from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FulfillmentJobRun(Base):
    __tablename__ = "fulfillment_job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    triggered_by: Mapped[str] = mapped_column(String(32), nullable=False)
    advanced_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
