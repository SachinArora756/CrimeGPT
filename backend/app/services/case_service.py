import random
import string
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case, CaseStatus
from app.schemas.case import CaseCreate, CaseUpdate


def generate_fir_number(station_id: str | None = None) -> str:
    prefix = station_id or "CG"
    year = datetime.utcnow().year
    random_part = "".join(random.choices(string.digits, k=4))
    return f"{prefix}/{random_part}/{year}"


async def create_case(db: AsyncSession, case_data: CaseCreate, officer_id: int) -> Case:
    fir_number = generate_fir_number(case_data.station_id)

    case = Case(
        fir_number=fir_number,
        complainant_name=case_data.complainant_name,
        complainant_contact=case_data.complainant_contact,
        complainant_address=case_data.complainant_address,
        accused_name=case_data.accused_name,
        incident_date=case_data.incident_date,
        incident_time=case_data.incident_time,
        incident_location=case_data.incident_location,
        description=case_data.description,
        offense_type=case_data.offense_type,
        station_id=case_data.station_id,
        assigned_officer_id=officer_id,
        status=CaseStatus.REGISTERED,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


async def get_case_by_id(db: AsyncSession, case_id: int) -> Case | None:
    result = await db.execute(select(Case).where(Case.id == case_id))
    return result.scalar_one_or_none()


async def get_cases(
    db: AsyncSession, page: int = 1, per_page: int = 20, status: CaseStatus | None = None, search: str | None = None
):
    query = select(Case)

    if status:
        query = query.where(Case.status == status)
    if search:
        query = query.where(
            Case.complainant_name.ilike(f"%{search}%")
            | Case.fir_number.ilike(f"%{search}%")
            | Case.description.ilike(f"%{search}%")
        )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Case.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    cases = result.scalars().all()

    return cases, total


async def update_case(db: AsyncSession, case_id: int, case_data: CaseUpdate) -> Case | None:
    case = await get_case_by_id(db, case_id)
    if not case:
        return None

    update_data = case_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)

    case.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(case)
    return case
