"""Normalize raw BuiltWith API responses into Pydantic models."""

from __future__ import annotations

from retina.models.normalized import TechStackData, Technology


def normalize_builtwith(raw: dict) -> TechStackData:
    """Transform a raw BuiltWith response into a TechStackData model.

    Deduplicates technologies across paths and extracts meta/social data.

    Args:
        raw: Raw JSON response from the BuiltWith API.

    Returns:
        Normalized TechStackData with technologies, meta, and social profiles.
    """
    results = raw.get("Results", [])
    if not results:
        return TechStackData()

    result = results[0].get("Result", {})
    paths = result.get("Paths", [])

    technologies: list[Technology] = []
    seen_names: set[str] = set()

    for path in paths:
        for tech in path.get("Technologies", []):
            name = tech.get("Name", "")
            if not name or name in seen_names:
                continue
            seen_names.add(name)

            # Categories come as a list of strings or empty
            categories = tech.get("Categories", [])
            if isinstance(categories, str):
                categories = [categories]

            technologies.append(
                Technology(
                    name=name,
                    description=tech.get("Description"),
                    link=tech.get("Link"),
                    categories=categories,
                    tag=tech.get("Tag"),
                )
            )

    # Extract meta information
    meta_raw = result.get("Meta", {})
    meta = {}
    if isinstance(meta_raw, dict):
        meta = {k: str(v) for k, v in meta_raw.items()}

    # Extract social profiles
    social = result.get("SocialProfiles", [])
    if not isinstance(social, list):
        social = []

    return TechStackData(
        technologies=technologies,
        meta=meta,
        social_profiles=social,
    )
