"""Services package.

A service orchestrates one or more repositories, enforces invariants,
and exposes the API used by routers. Routers must depend on services,
never on repositories or ORM sessions directly (apart from getting the
session via `Depends(get_db)` to construct the service).
"""

__all__: list[str] = []
