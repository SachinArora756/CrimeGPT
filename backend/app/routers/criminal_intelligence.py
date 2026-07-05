from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form, status
import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc
from datetime import datetime, timedelta

from app.database import get_db
from app.services.auth_service import get_current_user, require_min_role
from app.models.user import User, UserRole
from app.models.criminal_intelligence import (
    CriminalProfile, CriminalFaceEmbedding, CriminalFingerprint,
    CriminalDNAProfile, CriminalAlias, CriminalAddress, CriminalVehicle,
    CriminalPhoneNumber, CriminalSocialAccount, CriminalAssociate,
    CriminalCaseHistory, CriminalImage, CriminalDocument, CriminalTimeline,
    CriminalSearchLog, CriminalWatchlist,
    DangerLevel, WantedStatus, Gender,
)
from app.schemas.criminal_intelligence import (
    CriminalProfileCreate, CriminalProfileUpdate,
    CriminalProfileResponse, CriminalProfileDetailResponse,
    CriminalProfileListItem, CriminalProfileListResponse,
    CriminalStatsResponse,
    AssociateCreate, AssociateResponse,
    CaseHistoryCreate, CaseHistoryResponse,
    TimelineCreate, TimelineResponse,
    AddressCreate, AddressResponse,
    VehicleCreate, VehicleResponse,
    WatchlistCreate, WatchlistResponse,
    FaceEmbeddingResponse, FingerprintResponse,
    DNAProfileCreate, DNAProfileResponse,
)
from app.utils.rate_limiter import limiter

router = APIRouter()

role_dependency = Depends(require_min_role(UserRole.SUB_INSPECTOR))


# ─── Helper ─────────────────────────────────────────────────────────────────────

async def _get_criminal_by_criminal_id(
    db: AsyncSession, criminal_id: str
) -> CriminalProfile:
    """Fetch a criminal profile by its string criminal_id (e.g. 'CR-0001')."""
    result = await db.execute(
        select(CriminalProfile).where(CriminalProfile.criminal_id == criminal_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Criminal profile '{criminal_id}' not found",
        )
    return profile


async def _generate_criminal_id(db: AsyncSession) -> str:
    """Generate the next sequential criminal_id like CR-0001."""
    result = await db.execute(
        select(func.count()).select_from(CriminalProfile)
    )
    count = result.scalar() or 0
    return f"CR-{count + 1:04d}"


# ─── List Criminal Profiles ──────────────────────────────────────────────────────

@router.get("/", response_model=CriminalProfileListResponse)
@limiter.limit("60/minute")
async def list_criminals(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    wanted_status: WantedStatus | None = None,
    danger_level: DangerLevel | None = None,
    crime_category: str | None = Query(default=None, max_length=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """List criminal profiles with pagination, search, and filters."""
    query = select(CriminalProfile).where(CriminalProfile.is_active == True)

    # Text search
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                CriminalProfile.full_name.ilike(search_term),
                CriminalProfile.criminal_id.ilike(search_term),
                CriminalProfile.gang_name.ilike(search_term),
            )
        )

    # Filters
    if wanted_status:
        query = query.where(CriminalProfile.wanted_status == wanted_status)
    if danger_level:
        query = query.where(CriminalProfile.danger_level == danger_level)
    if crime_category:
        # JSON field search - crime_categories is stored as JSON array
        query = query.where(
            CriminalProfile.crime_categories.cast(str).ilike(f"%{crime_category}%")
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(desc(CriminalProfile.created_at))
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    profiles = result.scalars().all()

    # Build list items with primary image
    items = []
    for profile in profiles:
        # Get primary image URL
        img_result = await db.execute(
            select(CriminalImage.image_path).where(
                CriminalImage.criminal_id == profile.id,
                CriminalImage.is_primary == True,
            ).limit(1)
        )
        primary_image = img_result.scalar_one_or_none()

        items.append(CriminalProfileListItem(
            id=profile.id,
            criminal_id=profile.criminal_id,
            full_name=profile.full_name,
            nicknames=profile.nicknames,
            gender=profile.gender,
            wanted_status=profile.wanted_status,
            danger_level=profile.danger_level,
            gang_name=profile.gang_name,
            total_arrests=profile.total_arrests,
            total_firs=profile.total_firs,
            crime_categories=profile.crime_categories,
            primary_image_url=primary_image,
            created_at=profile.created_at,
        ))

    return CriminalProfileListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


# ─── Dashboard Stats ────────────────────────────────────────────────────────────

@router.get("/stats", response_model=CriminalStatsResponse)
@limiter.limit("30/minute")
async def get_criminal_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get criminal intelligence dashboard statistics."""
    base = select(CriminalProfile).where(CriminalProfile.is_active == True)

    # Total
    total_result = await db.execute(
        select(func.count()).select_from(base.subquery())
    )
    total = total_result.scalar() or 0

    # Wanted count
    wanted_result = await db.execute(
        select(func.count()).select_from(
            base.where(CriminalProfile.wanted_status.in_([
                WantedStatus.WANTED, WantedStatus.MOST_WANTED, WantedStatus.ABSCONDING
            ])).subquery()
        )
    )
    wanted = wanted_result.scalar() or 0

    # Most wanted count
    most_wanted_result = await db.execute(
        select(func.count()).select_from(
            base.where(CriminalProfile.wanted_status == WantedStatus.MOST_WANTED).subquery()
        )
    )
    most_wanted = most_wanted_result.scalar() or 0

    # By danger level
    danger_result = await db.execute(
        select(CriminalProfile.danger_level, func.count())
        .where(CriminalProfile.is_active == True)
        .group_by(CriminalProfile.danger_level)
    )
    by_danger_level = {row[0].value: row[1] for row in danger_result.all()}

    # Top gangs
    gang_result = await db.execute(
        select(CriminalProfile.gang_name, func.count().label("count"))
        .where(
            CriminalProfile.is_active == True,
            CriminalProfile.gang_name.isnot(None),
            CriminalProfile.gang_name != "",
        )
        .group_by(CriminalProfile.gang_name)
        .order_by(desc("count"))
        .limit(10)
    )
    top_gangs = [{"name": row[0], "count": row[1]} for row in gang_result.all()]

    # Top crime categories - since it's JSON, we count profiles per category
    # Simple approach: get all profiles and aggregate in Python
    cat_result = await db.execute(
        select(CriminalProfile.crime_categories)
        .where(
            CriminalProfile.is_active == True,
            CriminalProfile.crime_categories.isnot(None),
        )
    )
    category_counts: dict[str, int] = {}
    for row in cat_result.all():
        categories = row[0]
        if isinstance(categories, list):
            for cat in categories:
                if isinstance(cat, str):
                    category_counts[cat] = category_counts.get(cat, 0) + 1
    top_categories = sorted(
        [{"category": k, "count": v} for k, v in category_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    # Recent additions (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_result = await db.execute(
        select(func.count()).select_from(
            base.where(CriminalProfile.created_at >= thirty_days_ago).subquery()
        )
    )
    recent_additions = recent_result.scalar() or 0

    return CriminalStatsResponse(
        total=total,
        wanted=wanted,
        most_wanted=most_wanted,
        by_danger_level=by_danger_level,
        top_gangs=top_gangs,
        top_categories=top_categories,
        recent_additions=recent_additions,
    )


# ─── Watchlist (must be before /{criminal_id} to avoid route conflict) ──────────

@router.get("/watchlist", response_model=list[WatchlistResponse])
@limiter.limit("60/minute")
async def get_watchlist(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get active watchlist entries with criminal name."""
    result = await db.execute(
        select(CriminalWatchlist)
        .where(CriminalWatchlist.is_active == True)
        .order_by(desc(CriminalWatchlist.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    entries = result.scalars().all()

    items = []
    for entry in entries:
        profile_result = await db.execute(
            select(CriminalProfile.full_name, CriminalProfile.criminal_id)
            .where(CriminalProfile.id == entry.criminal_id)
        )
        profile_row = profile_result.first()
        resp = WatchlistResponse.model_validate(entry)
        if profile_row:
            resp.criminal_name = profile_row[0]
            resp.criminal_profile_id = profile_row[1]
        items.append(resp)

    return items


@router.post("/watchlist", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def add_to_watchlist(
    request: Request,
    data: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Add a criminal to the watchlist."""
    criminal_result = await db.execute(
        select(CriminalProfile).where(CriminalProfile.id == data.criminal_id)
    )
    if criminal_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Criminal profile not found",
        )

    existing = await db.execute(
        select(CriminalWatchlist).where(
            CriminalWatchlist.criminal_id == data.criminal_id,
            CriminalWatchlist.is_active == True,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Criminal is already on the active watchlist",
        )

    entry = CriminalWatchlist(
        criminal_id=data.criminal_id,
        added_by=current_user.id,
        reason=data.reason,
        priority=data.priority,
        alert_on_match=data.alert_on_match,
        expires_at=data.expires_at,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return WatchlistResponse.model_validate(entry)


@router.delete("/watchlist/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def remove_from_watchlist(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Remove a criminal from the watchlist (soft-delete by deactivating)."""
    result = await db.execute(
        select(CriminalWatchlist).where(CriminalWatchlist.id == id)
    )
    entry = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist entry not found",
        )

    entry.is_active = False
    await db.commit()
    return None


# ─── Get Criminal Profile Detail ────────────────────────────────────────────────

@router.get("/{criminal_id}", response_model=CriminalProfileDetailResponse)
@limiter.limit("60/minute")
async def get_criminal_profile(
    request: Request,
    criminal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get full criminal profile with all related data."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)

    # Fetch related data counts and records
    face_count = await db.execute(
        select(func.count()).where(CriminalFaceEmbedding.criminal_id == profile.id)
    )
    fp_count = await db.execute(
        select(func.count()).where(CriminalFingerprint.criminal_id == profile.id)
    )
    dna_count = await db.execute(
        select(func.count()).where(CriminalDNAProfile.criminal_id == profile.id)
    )

    aliases_result = await db.execute(
        select(CriminalAlias).where(CriminalAlias.criminal_id == profile.id)
    )
    addresses_result = await db.execute(
        select(CriminalAddress).where(CriminalAddress.criminal_id == profile.id)
    )
    vehicles_result = await db.execute(
        select(CriminalVehicle).where(CriminalVehicle.criminal_id == profile.id)
    )
    phones_result = await db.execute(
        select(CriminalPhoneNumber).where(CriminalPhoneNumber.criminal_id == profile.id)
    )
    socials_result = await db.execute(
        select(CriminalSocialAccount).where(CriminalSocialAccount.criminal_id == profile.id)
    )
    associates_result = await db.execute(
        select(CriminalAssociate).where(CriminalAssociate.criminal_id == profile.id)
    )
    cases_result = await db.execute(
        select(CriminalCaseHistory).where(CriminalCaseHistory.criminal_id == profile.id)
            .order_by(desc(CriminalCaseHistory.date_of_offense))
    )
    images_result = await db.execute(
        select(CriminalImage).where(CriminalImage.criminal_id == profile.id)
    )
    timeline_result = await db.execute(
        select(CriminalTimeline).where(CriminalTimeline.criminal_id == profile.id)
            .order_by(desc(CriminalTimeline.event_date))
    )

    def _to_dict_list(scalars):
        from sqlalchemy import inspect as sa_inspect
        items = []
        for item in scalars:
            mapper = sa_inspect(type(item))
            d = {}
            for attr in mapper.column_attrs:
                col_name = attr.columns[0].name
                d[col_name] = getattr(item, attr.key)
            for k, v in d.items():
                if isinstance(v, datetime):
                    d[k] = v.isoformat()
                elif hasattr(v, "isoformat"):
                    d[k] = v.isoformat()
            items.append(d)
        return items

    return CriminalProfileDetailResponse(
        id=profile.id,
        criminal_id=profile.criminal_id,
        full_name=profile.full_name,
        father_name=profile.father_name,
        nicknames=profile.nicknames,
        date_of_birth=profile.date_of_birth,
        gender=profile.gender,
        nationality=profile.nationality,
        religion=profile.religion,
        caste=profile.caste,
        occupation=profile.occupation,
        education=profile.education,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        build=profile.build,
        complexion=profile.complexion,
        hair_color=profile.hair_color,
        eye_color=profile.eye_color,
        identifying_marks=profile.identifying_marks,
        gang_name=profile.gang_name,
        gang_role=profile.gang_role,
        crime_categories=profile.crime_categories,
        modus_operandi=profile.modus_operandi,
        known_weapons=profile.known_weapons,
        wanted_status=profile.wanted_status,
        danger_level=profile.danger_level,
        reward_amount=profile.reward_amount,
        total_arrests=profile.total_arrests,
        total_convictions=profile.total_convictions,
        total_firs=profile.total_firs,
        first_offense_date=profile.first_offense_date,
        last_known_activity=profile.last_known_activity,
        prison_history=profile.prison_history,
        court_cases=profile.court_cases,
        bail_status=profile.bail_status,
        notes=profile.notes,
        is_active=profile.is_active,
        added_by=profile.added_by,
        station_id=profile.station_id,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        face_embeddings_count=face_count.scalar() or 0,
        fingerprints_count=fp_count.scalar() or 0,
        dna_profiles_count=dna_count.scalar() or 0,
        aliases=_to_dict_list(aliases_result.scalars().all()),
        addresses=_to_dict_list(addresses_result.scalars().all()),
        vehicles=_to_dict_list(vehicles_result.scalars().all()),
        phone_numbers=_to_dict_list(phones_result.scalars().all()),
        social_accounts=_to_dict_list(socials_result.scalars().all()),
        associates=_to_dict_list(associates_result.scalars().all()),
        case_history=_to_dict_list(cases_result.scalars().all()),
        images=_to_dict_list(images_result.scalars().all()),
        timeline=_to_dict_list(timeline_result.scalars().all()),
    )


# ─── Create Criminal Profile ────────────────────────────────────────────────────

@router.post("/", response_model=CriminalProfileResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_criminal_profile(
    request: Request,
    data: CriminalProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Create a new criminal profile."""
    criminal_id = await _generate_criminal_id(db)

    profile = CriminalProfile(
        criminal_id=criminal_id,
        full_name=data.full_name,
        father_name=data.father_name,
        nicknames=data.nicknames,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        nationality=data.nationality,
        religion=data.religion,
        caste=data.caste,
        occupation=data.occupation,
        education=data.education,
        height_cm=data.height_cm,
        weight_kg=data.weight_kg,
        build=data.build,
        complexion=data.complexion,
        hair_color=data.hair_color,
        eye_color=data.eye_color,
        identifying_marks=data.identifying_marks,
        gang_name=data.gang_name,
        gang_role=data.gang_role,
        crime_categories=data.crime_categories,
        modus_operandi=data.modus_operandi,
        known_weapons=data.known_weapons,
        wanted_status=data.wanted_status,
        danger_level=data.danger_level,
        reward_amount=data.reward_amount,
        total_arrests=data.total_arrests,
        total_convictions=data.total_convictions,
        total_firs=data.total_firs,
        first_offense_date=data.first_offense_date,
        prison_history=data.prison_history,
        court_cases=data.court_cases,
        bail_status=data.bail_status,
        notes=data.notes,
        station_id=data.station_id,
        added_by=current_user.id,
    )

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return CriminalProfileResponse.model_validate(profile)


# ─── Update Criminal Profile ────────────────────────────────────────────────────

@router.put("/{criminal_id}", response_model=CriminalProfileResponse)
@limiter.limit("30/minute")
async def update_criminal_profile(
    request: Request,
    criminal_id: str,
    data: CriminalProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Update an existing criminal profile."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    profile.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(profile)

    return CriminalProfileResponse.model_validate(profile)


# ─── Delete (Soft) Criminal Profile ─────────────────────────────────────────────

@router.delete("/{criminal_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def deactivate_criminal_profile(
    request: Request,
    criminal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Soft-delete a criminal profile by marking it inactive."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)
    profile.is_active = False
    profile.updated_at = datetime.utcnow()
    await db.commit()
    return None


# ─── Associates ──────────────────────────────────────────────────────────────────

@router.get("/{criminal_id}/associates", response_model=list[AssociateResponse])
@limiter.limit("60/minute")
async def get_associates(
    request: Request,
    criminal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get all associates of a criminal."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)
    result = await db.execute(
        select(CriminalAssociate).where(CriminalAssociate.criminal_id == profile.id)
    )
    associates = result.scalars().all()
    return [AssociateResponse.model_validate(a) for a in associates]


@router.post(
    "/{criminal_id}/associates",
    response_model=AssociateResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def add_associate(
    request: Request,
    criminal_id: str,
    data: AssociateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Add an associate to a criminal profile."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)

    associate = CriminalAssociate(
        criminal_id=profile.id,
        associate_criminal_id=data.associate_criminal_id,
        associate_name=data.associate_name,
        relationship_type=data.relationship_type,
        gang_connection=data.gang_connection,
        notes=data.notes,
    )
    db.add(associate)
    await db.commit()
    await db.refresh(associate)

    return AssociateResponse.model_validate(associate)


# ─── Case History ────────────────────────────────────────────────────────────────

@router.get("/{criminal_id}/case-history", response_model=list[CaseHistoryResponse])
@limiter.limit("60/minute")
async def get_case_history(
    request: Request,
    criminal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get case history for a criminal."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)
    result = await db.execute(
        select(CriminalCaseHistory)
        .where(CriminalCaseHistory.criminal_id == profile.id)
        .order_by(desc(CriminalCaseHistory.date_of_offense))
    )
    cases = result.scalars().all()
    return [CaseHistoryResponse.model_validate(c) for c in cases]


@router.post(
    "/{criminal_id}/case-history",
    response_model=CaseHistoryResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def add_case_history(
    request: Request,
    criminal_id: str,
    data: CaseHistoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Add a case history entry to a criminal profile."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)

    entry = CriminalCaseHistory(
        criminal_id=profile.id,
        fir_number=data.fir_number,
        case_type=data.case_type,
        sections_applied=data.sections_applied,
        police_station=data.police_station,
        district=data.district,
        state=data.state,
        date_of_offense=data.date_of_offense,
        date_of_arrest=data.date_of_arrest,
        court_name=data.court_name,
        case_status=data.case_status,
        verdict=data.verdict,
        sentence=data.sentence,
        bail_granted=data.bail_granted,
        description=data.description,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return CaseHistoryResponse.model_validate(entry)


# ─── Timeline ────────────────────────────────────────────────────────────────────

@router.get("/{criminal_id}/timeline", response_model=list[TimelineResponse])
@limiter.limit("60/minute")
async def get_timeline(
    request: Request,
    criminal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get timeline events for a criminal."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)
    result = await db.execute(
        select(CriminalTimeline)
        .where(CriminalTimeline.criminal_id == profile.id)
        .order_by(desc(CriminalTimeline.event_date))
    )
    events = result.scalars().all()
    return [TimelineResponse.model_validate(e) for e in events]


@router.post(
    "/{criminal_id}/timeline",
    response_model=TimelineResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def add_timeline_event(
    request: Request,
    criminal_id: str,
    data: TimelineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Add a timeline event to a criminal profile."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)

    event = CriminalTimeline(
        criminal_id=profile.id,
        event_date=data.event_date,
        event_type=data.event_type,
        title=data.title,
        description=data.description,
        location=data.location,
        extra_data=data.metadata,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return TimelineResponse.model_validate(event)


# ─── Addresses ───────────────────────────────────────────────────────────────────

@router.get("/{criminal_id}/addresses", response_model=list[AddressResponse])
@limiter.limit("60/minute")
async def get_addresses(
    request: Request,
    criminal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get all addresses for a criminal."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)
    result = await db.execute(
        select(CriminalAddress).where(CriminalAddress.criminal_id == profile.id)
    )
    addresses = result.scalars().all()
    return [AddressResponse.model_validate(a) for a in addresses]


@router.post(
    "/{criminal_id}/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def add_address(
    request: Request,
    criminal_id: str,
    data: AddressCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Add an address to a criminal profile."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)

    address = CriminalAddress(
        criminal_id=profile.id,
        address_type=data.address_type,
        address_line=data.address_line,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        is_current=data.is_current,
        verified=data.verified,
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)

    return AddressResponse.model_validate(address)


# ─── Vehicles ────────────────────────────────────────────────────────────────────

@router.get("/{criminal_id}/vehicles", response_model=list[VehicleResponse])
@limiter.limit("60/minute")
async def get_vehicles(
    request: Request,
    criminal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get all vehicles associated with a criminal."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)
    result = await db.execute(
        select(CriminalVehicle).where(CriminalVehicle.criminal_id == profile.id)
    )
    vehicles = result.scalars().all()
    return [VehicleResponse.model_validate(v) for v in vehicles]


@router.post(
    "/{criminal_id}/vehicles",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def add_vehicle(
    request: Request,
    criminal_id: str,
    data: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Add a vehicle to a criminal profile."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)

    vehicle = CriminalVehicle(
        criminal_id=profile.id,
        vehicle_type=data.vehicle_type,
        make=data.make,
        model=data.model,
        color=data.color,
        registration_number=data.registration_number,
        chassis_number=data.chassis_number,
        is_stolen=data.is_stolen,
        notes=data.notes,
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)

    return VehicleResponse.model_validate(vehicle)


# ─── Biometric Search Placeholders ──────────────────────────────────────────────

@router.get("/search/face")
@limiter.limit("10/minute")
async def search_by_face(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Placeholder for face recognition search. Actual implementation pending."""
    return {
        "message": "Face search endpoint - implementation pending",
        "status": "placeholder",
        "results": [],
        "note": "Upload a face image via the dedicated upload endpoint for matching.",
    }


@router.get("/search/fingerprint")
@limiter.limit("10/minute")
async def search_by_fingerprint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Placeholder for fingerprint search. Actual implementation pending."""
    return {
        "message": "Fingerprint search endpoint - implementation pending",
        "status": "placeholder",
        "results": [],
        "note": "Upload fingerprint data via the dedicated upload endpoint for matching.",
    }


@router.get("/search/dna/{dna_id}")
@limiter.limit("10/minute")
async def search_by_dna(
    request: Request,
    dna_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Search for a criminal profile by DNA ID."""
    result = await db.execute(
        select(CriminalDNAProfile).where(CriminalDNAProfile.dna_id == dna_id)
    )
    dna_record = result.scalar_one_or_none()

    if dna_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No DNA record found for ID '{dna_id}'",
        )

    # Get the associated criminal profile
    profile_result = await db.execute(
        select(CriminalProfile).where(CriminalProfile.id == dna_record.criminal_id)
    )
    profile = profile_result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated criminal profile not found",
        )

    # Log the search
    search_log = CriminalSearchLog(
        user_id=current_user.id,
        search_type="dna",
        search_query=dna_id,
        results_count=1,
        top_match_id=profile.id,
        top_match_confidence=1.0,
        ip_address=request.client.host if request.client else None,
    )
    db.add(search_log)
    await db.commit()

    return {
        "match_found": True,
        "criminal_id": profile.criminal_id,
        "full_name": profile.full_name,
        "danger_level": profile.danger_level.value,
        "wanted_status": profile.wanted_status.value,
        "dna_record": {
            "dna_id": dna_record.dna_id,
            "sample_number": dna_record.sample_number,
            "laboratory": dna_record.laboratory,
            "collection_date": dna_record.collection_date.isoformat() if dna_record.collection_date else None,
        },
    }


# ─── Biometric Records Per Criminal ─────────────────────────────────────────────

@router.get("/{criminal_id}/biometrics/faces")
@limiter.limit("60/minute")
async def get_face_embeddings(
    request: Request,
    criminal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get all face embedding records for a criminal."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)
    result = await db.execute(
        select(CriminalFaceEmbedding).where(CriminalFaceEmbedding.criminal_id == profile.id)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "image_path": r.image_path,
            "model_name": r.model_name,
            "embedding_dim": r.embedding_dim,
            "embedding": r.embedding,
            "quality_score": r.quality_score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get("/{criminal_id}/biometrics/fingerprints")
@limiter.limit("60/minute")
async def get_fingerprints(
    request: Request,
    criminal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get all fingerprint records for a criminal."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)
    result = await db.execute(
        select(CriminalFingerprint).where(CriminalFingerprint.criminal_id == profile.id)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "finger_type": r.finger_type,
            "image_path": r.image_path,
            "template_data": r.template_data,
            "quality_score": r.quality_score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get("/{criminal_id}/biometrics/dna")
@limiter.limit("60/minute")
async def get_dna_profiles(
    request: Request,
    criminal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Get all DNA profile records for a criminal."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)
    result = await db.execute(
        select(CriminalDNAProfile).where(CriminalDNAProfile.criminal_id == profile.id)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "dna_id": r.dna_id,
            "sample_number": r.sample_number,
            "laboratory": r.laboratory,
            "collection_date": r.collection_date.isoformat() if r.collection_date else None,
            "profile_data": r.profile_data,
            "loci_markers": r.loci_markers,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


# ─── Biometric Upload Endpoints ───────────────────────────────────────────────

BIOMETRICS_DIR = "data/criminal-biometrics"
MAX_BIOMETRIC_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/bmp", "image/tiff", "image/webp"}


@router.post(
    "/{criminal_id}/biometrics/faces",
    response_model=FaceEmbeddingResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def add_face_embedding(
    request: Request,
    criminal_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Upload a face image, extract embedding via InsightFace, and store it."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Allowed: {sorted(ALLOWED_IMAGE_TYPES)}",
        )

    content = await file.read()
    if len(content) > MAX_BIOMETRIC_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum 10 MB.",
        )

    face_dir = os.path.join(BIOMETRICS_DIR, "faces", criminal_id)
    os.makedirs(face_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "face.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(face_dir, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        from app.services.biometric_service import generate_face_embedding, upsert_face_to_qdrant
        embedding, quality_score = await generate_face_embedding(file_path)
    except ValueError as e:
        os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face embedding extraction failed: {str(e)}",
        )

    record = CriminalFaceEmbedding(
        criminal_id=profile.id,
        embedding=embedding,
        image_path=file_path,
        model_name="insightface_buffalo",
        embedding_dim=512,
        quality_score=quality_score,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    try:
        upsert_face_to_qdrant(
            point_id=record.id,
            embedding=embedding,
            criminal_db_id=profile.id,
            criminal_public_id=profile.criminal_id,
            full_name=profile.full_name,
            image_path=file_path,
            wanted_status=profile.wanted_status.value if profile.wanted_status else None,
            danger_level=profile.danger_level.value if profile.danger_level else None,
            gang_name=profile.gang_name,
        )
    except Exception:
        pass

    return FaceEmbeddingResponse.model_validate(record)


@router.post(
    "/{criminal_id}/biometrics/fingerprints",
    response_model=FingerprintResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def add_fingerprint(
    request: Request,
    criminal_id: str,
    file: UploadFile = File(...),
    finger_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Upload a fingerprint image, extract ORB template, and store it."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Allowed: {sorted(ALLOWED_IMAGE_TYPES)}",
        )

    valid_finger_types = {
        "right_thumb", "right_index", "right_middle", "right_ring", "right_little",
        "left_thumb", "left_index", "left_middle", "left_ring", "left_little",
    }
    if finger_type not in valid_finger_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid finger_type '{finger_type}'. Allowed: {sorted(valid_finger_types)}",
        )

    content = await file.read()
    if len(content) > MAX_BIOMETRIC_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum 10 MB.",
        )

    fp_dir = os.path.join(BIOMETRICS_DIR, "fingerprints", criminal_id)
    os.makedirs(fp_dir, exist_ok=True)

    ext = os.path.splitext(file.filename or "fingerprint.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(fp_dir, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        from app.services.biometric_service import generate_fingerprint_template
        template_data, quality_score = await generate_fingerprint_template(file_path)
    except ValueError as e:
        os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fingerprint template extraction failed: {str(e)}",
        )

    record = CriminalFingerprint(
        criminal_id=profile.id,
        finger_type=finger_type,
        template_data=template_data,
        image_path=file_path,
        quality_score=quality_score,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return FingerprintResponse.model_validate(record)


@router.post(
    "/{criminal_id}/biometrics/dna",
    response_model=DNAProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def add_dna_profile(
    request: Request,
    criminal_id: str,
    data: DNAProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = role_dependency,
):
    """Add a DNA profile record to a criminal."""
    profile = await _get_criminal_by_criminal_id(db, criminal_id)

    existing = await db.execute(
        select(CriminalDNAProfile).where(CriminalDNAProfile.dna_id == data.dna_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"DNA profile with ID '{data.dna_id}' already exists.",
        )

    record = CriminalDNAProfile(
        criminal_id=profile.id,
        dna_id=data.dna_id,
        sample_number=data.sample_number,
        laboratory=data.laboratory,
        collection_date=data.collection_date,
        profile_data=data.profile_data,
        loci_markers=data.loci_markers,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return DNAProfileResponse.model_validate(record)


