"""Shared column-ratio constants so every page uses the same grammar.
Use these instead of inlining ratios in st.columns([...])."""
GRID_WIDE_SIDEBAR = [2, 1]        # 66/33 — chart + sidebar (default)
GRID_BALANCED     = [1, 1]        # 50/50
GRID_NARROW_WIDE  = [1, 2]        # 33/66 — use sparingly, prefer inverting content
GRID_THIRDS       = [1, 1, 1]     # 3 equal
GRID_FOURTHS      = [1, 1, 1, 1]  # 4 equal (KPI strips)
GRID_3COL_FOCUS   = [2, 1, 1]     # lead + 2 supporting
