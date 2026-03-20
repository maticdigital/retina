"""Standards library endpoints — CRUD for retina_standards."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query

from api.deps import CurrentUser, get_supabase

router = APIRouter(prefix="/standards", tags=["standards"])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _require_admin(user: dict[str, Any]) -> None:
    if user["role"] not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


# ── Models ───────────────────────────────────────────────────────────────────

class StandardOut(BaseModel):
    id: str
    lens: str
    category: str
    principle: str
    source: str
    source_url: str | None = None
    evaluation_criteria: str
    scoring_guidance: str
    applies_to_cohort: bool = True
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None


class StandardCreate(BaseModel):
    lens: str
    category: str
    principle: str
    source: str
    source_url: str | None = None
    evaluation_criteria: str
    scoring_guidance: str
    applies_to_cohort: bool = True


class StandardUpdate(BaseModel):
    lens: str | None = None
    category: str | None = None
    principle: str | None = None
    source: str | None = None
    source_url: str | None = None
    evaluation_criteria: str | None = None
    scoring_guidance: str | None = None
    applies_to_cohort: bool | None = None
    is_active: bool | None = None


class StandardsResponse(BaseModel):
    lens: str
    count: int
    standards: list[StandardOut]


# ── Public read endpoint ─────────────────────────────────────────────────────

@router.get("", response_model=StandardsResponse)
def get_standards(
    user: CurrentUser,
    lens: str = Query(..., description="Lens name: performance, seo, brand, experience, conversion"),
    category: str | None = Query(None, description="Filter by category within a lens"),
    cohort_only: bool = Query(False, description="Only return entries where applies_to_cohort = true"),
):
    """Return all active standards for a given lens."""
    valid_lenses = {"performance", "seo", "brand", "experience", "conversion"}
    if lens not in valid_lenses:
        raise HTTPException(status_code=400, detail=f"Invalid lens. Must be one of: {', '.join(sorted(valid_lenses))}")

    sb = get_supabase()
    query = sb.table("retina_standards").select("*").eq("lens", lens).eq("is_active", True)

    if category:
        query = query.eq("category", category)
    if cohort_only:
        query = query.eq("applies_to_cohort", True)

    query = query.order("category").order("created_at")
    resp = query.execute()

    return StandardsResponse(
        lens=lens,
        count=len(resp.data or []),
        standards=resp.data or [],
    )


# ── Admin CRUD endpoints ────────────────────────────────────────────────────

@router.get("/all", response_model=list[StandardOut])
def list_all_standards(user: CurrentUser):
    """Return ALL standards (including inactive) for admin management."""
    _require_admin(user)
    sb = get_supabase()
    resp = sb.table("retina_standards").select("*").order("lens").order("category").order("created_at").execute()
    return resp.data or []


@router.post("", response_model=StandardOut, status_code=201)
def create_standard(body: StandardCreate, user: CurrentUser):
    """Create a new standard entry (admin/owner only)."""
    _require_admin(user)

    valid_lenses = {"performance", "seo", "brand", "experience", "conversion"}
    if body.lens not in valid_lenses:
        raise HTTPException(status_code=400, detail=f"Invalid lens. Must be one of: {', '.join(sorted(valid_lenses))}")

    sb = get_supabase()
    resp = sb.table("retina_standards").insert(body.model_dump(exclude_none=True)).execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create standard")

    return resp.data[0]


@router.put("/{standard_id}", response_model=StandardOut)
def update_standard(standard_id: str, body: StandardUpdate, user: CurrentUser):
    """Update an existing standard (admin/owner only)."""
    _require_admin(user)
    sb = get_supabase()

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "lens" in updates:
        valid_lenses = {"performance", "seo", "brand", "experience", "conversion"}
        if updates["lens"] not in valid_lenses:
            raise HTTPException(status_code=400, detail=f"Invalid lens. Must be one of: {', '.join(sorted(valid_lenses))}")

    resp = sb.table("retina_standards").update(updates).eq("id", standard_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Standard not found")

    return resp.data[0]


@router.delete("/{standard_id}", status_code=204)
def delete_standard(standard_id: str, user: CurrentUser):
    """Hard-delete a standard (admin/owner only). Prefer toggling is_active instead."""
    _require_admin(user)
    sb = get_supabase()
    sb.table("retina_standards").delete().eq("id", standard_id).execute()


@router.get("/summary")
def standards_summary(user: CurrentUser):
    """Return count of active standards per lens."""
    _require_admin(user)
    sb = get_supabase()
    resp = sb.table("retina_standards").select("lens, is_active").execute()

    counts: dict[str, dict[str, int]] = {}
    for row in (resp.data or []):
        lens = row["lens"]
        if lens not in counts:
            counts[lens] = {"active": 0, "inactive": 0}
        if row["is_active"]:
            counts[lens]["active"] += 1
        else:
            counts[lens]["inactive"] += 1

    return {"counts": counts, "total": len(resp.data or [])}
