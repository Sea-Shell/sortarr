"""sortarr.filters — Individual filter implementations.

Each module registers its filter(s) with the chain engine at import time.
Import this package to activate all registrations.
"""

from sortarr.filters import (  # noqa: F401 — trigger registration
    ignore_list,
    word_filter,
    db_exists,
    title_similarity,
    selector_filter,
)
