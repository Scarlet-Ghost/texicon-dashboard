"""Pure HTML/JS string generators for loading, skeletons, and KPI count-up.

Functions return strings — they are wrapped in st.markdown(unsafe_allow_html=True)
by callers. Any motion is gated by prefers-reduced-motion via the CSS in theme.py.
"""


def loading_overlay_html() -> str:
    """Full-screen overlay shown during initial app boot."""
    return (
        '<div class="tx-loading-overlay" id="tx-loading-overlay">'
        '<div class="tx-brand" style="font-size:28px">'
        'TEXICON<span class="tx-leaf"></span>'
        '</div>'
        '<div class="tx-loading-bar"></div>'
        '</div>'
    )


def hide_loading_script() -> str:
    """Inline script to hide the overlay once Streamlit content paints."""
    return (
        '<script>'
        'requestAnimationFrame(function(){'
        '  var el=document.getElementById("tx-loading-overlay");'
        '  if(el){el.style.transition="opacity 200ms ease";el.style.opacity="0";'
        '         setTimeout(function(){el.remove();},220);}'
        '});'
        '</script>'
    )


def skeleton_block(width: str = "100%", height: str = "60px",
                   radius: str = "12px") -> str:
    return (
        f'<div class="tx-skeleton" '
        f'style="width:{width};height:{height};border-radius:{radius};"></div>'
    )


def count_up_value(label: str, value: str, numeric_target: float,
                   prefix: str = "", suffix: str = "") -> str:
    """Render a KPI value span with data attrs for the count-up runtime."""
    return (
        f'<span class="tx-kpi-val" '
        f'data-tx-count-target="{int(numeric_target)}" '
        f'data-tx-count-prefix="{prefix}" '
        f'data-tx-count-suffix="{suffix}" '
        f'aria-label="{label}: {value}">{value}</span>'
    )


def count_up_runtime_script() -> str:
    """Render once per page. Animates any [data-tx-count-target] from 0 to target."""
    return """<script>
(function(){
  if (window.__txCountInit) return; window.__txCountInit = true;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function fmt(n, prefix, suffix){
    if (n >= 1e6) return prefix + (n/1e6).toFixed(2) + 'M' + suffix;
    if (n >= 1e3) return prefix + (n/1e3).toFixed(1) + 'K' + suffix;
    return prefix + Math.round(n).toLocaleString() + suffix;
  }
  function animate(el){
    var target = parseFloat(el.getAttribute('data-tx-count-target'));
    var prefix = el.getAttribute('data-tx-count-prefix') || '';
    var suffix = el.getAttribute('data-tx-count-suffix') || '';
    if (reduce || isNaN(target)) { return; }
    var start = performance.now(), dur = 450;
    function tick(t){
      var p = Math.min(1, (t-start)/dur);
      var eased = 1 - Math.pow(1-p, 3);
      el.textContent = fmt(target * eased, prefix, suffix);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  document.querySelectorAll('[data-tx-count-target]').forEach(animate);
})();
</script>"""
