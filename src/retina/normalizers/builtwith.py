"""Normalize raw BuiltWith API responses into Pydantic models."""

from __future__ import annotations

from retina.models.normalized import TechStackData, Technology


def _is_currently_live(tech: dict) -> bool:
    """Check whether a BuiltWith technology entry is currently live.

    BuiltWith API includes both current and historical detections.
    A technology is considered currently live if:
    - It has no IsPremium/CurrentlyLive field (older API formats — assume live)
    - CurrentlyLive is explicitly > 0
    - LastDetected is 0 (still active) or within the last ~6 months

    We filter out entries where CurrentlyLive == 0 or where LastDetected
    is far in the past, indicating the tech is no longer present.
    """
    import time

    # CurrentlyLive: 0 = historical only, >0 = actively detected now
    currently_live = tech.get("CurrentlyLive")
    if currently_live is not None:
        return currently_live > 0

    # Fallback: check LastDetected timestamp (milliseconds since epoch).
    # If LastDetected is 0 the tech is still live. If it's a recent timestamp
    # (within the last 6 months) it's still considered current.
    last = tech.get("LastDetected", 0)
    if last == 0:
        return True

    # Convert ms epoch to seconds and compare to ~6 months ago
    six_months_ago = (time.time() - 180 * 86400) * 1000
    return last >= six_months_ago


# CMS category names used by BuiltWith
_CMS_CATEGORIES = frozenset({
    "CMS", "Hosted Solution", "Headless", "Enterprise",
    "Blog", "Ecommerce", "Wiki",
})

# Known CMS platform names for direct matching
_CMS_NAMES = frozenset({
    "Webflow", "WordPress", "Contentful", "Shopify", "Squarespace",
    "Wix", "Drupal", "Joomla", "Ghost", "Strapi", "Sanity",
    "Prismic", "Kentico", "Sitecore", "Adobe Experience Manager",
    "HubSpot CMS", "BigCommerce", "Magento", "PrestaShop",
})


def _is_cms(tech: dict) -> bool:
    """Check if a technology entry is a CMS platform."""
    name = tech.get("Name", "")
    if name in _CMS_NAMES:
        return True
    categories = tech.get("Categories", [])
    if isinstance(categories, str):
        categories = [categories]
    return bool(_CMS_CATEGORIES & set(categories))


def normalize_builtwith(raw: dict) -> TechStackData:
    """Transform a raw BuiltWith response into a TechStackData model.

    Only includes technologies that are CURRENTLY and ACTIVELY detected
    on the live site. Historical/previous detections are filtered out.

    For CMS platforms specifically, if multiple are detected, a
    'cms_conflict' flag is set in meta for analyst review.

    Args:
        raw: Raw JSON response from the BuiltWith API.

    Returns:
        Normalized TechStackData with technologies, meta, and social profiles.
    """
    results = raw.get("Results", [])
    if not results:
        return TechStackData()

    top_result = results[0]
    result = top_result.get("Result", {})
    paths = result.get("Paths", [])

    technologies: list[Technology] = []
    seen_names: set[str] = set()
    detected_cms: list[str] = []

    for path in paths:
        for tech in path.get("Technologies", []):
            name = tech.get("Name", "")
            if not name or name in seen_names:
                continue

            # Skip historical/non-live detections
            if not _is_currently_live(tech):
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

            # Track CMS detections
            if _is_cms(tech):
                detected_cms.append(name)

    # Extract meta information — lives at top_result level, not inner Result
    meta_raw = top_result.get("Meta", {})
    meta = {}
    if isinstance(meta_raw, dict):
        meta = {k: str(v) for k, v in meta_raw.items() if not isinstance(v, (list, dict))}

    # Flag multiple CMS detections for analyst review
    if len(detected_cms) > 1:
        meta["cms_conflict"] = "true"
        meta["cms_detected"] = ", ".join(sorted(detected_cms))

    # Extract social profiles — nested inside Meta.Social
    social = meta_raw.get("Social", []) if isinstance(meta_raw, dict) else []
    if not isinstance(social, list):
        social = []

    return TechStackData(
        technologies=technologies,
        meta=meta,
        social_profiles=social,
    )
