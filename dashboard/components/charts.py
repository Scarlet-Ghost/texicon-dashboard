import plotly.graph_objects as go
import plotly.express as px
import copy
import numpy as np
from data.constants import (
    CHART_COLORS, PHP_SYMBOL, PLOTLY_LAYOUT, BG_CARD, BORDER,
    TEXT_PRIMARY, TEXT_SECONDARY, PHP_TICK_FORMAT, PHP_TICK_PREFIX,
)

try:
    from components.theme import get_theme, current_theme
except ModuleNotFoundError:
    from dashboard.components.theme import get_theme, current_theme

_BRAND_PALETTE = ["#2d8a3e", "#FFC907", "#000000", "#888888",
                  "#1a5d27", "#9a7100", "#dc2626"]


def apply_theme(fig, mode=None):
    """Apply current theme template + brand palette to a Plotly figure."""
    mode = mode or current_theme()
    t = get_theme(mode)
    fig.update_layout(
        template=t["_plotly_template"],
        font=dict(family="-apple-system, Inter, system-ui",
                  size=11, color=t["text_primary"]),
        paper_bgcolor=t["bg_surface"],
        plot_bgcolor=t["bg_surface"],
        colorway=_BRAND_PALETTE,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    fig.update_xaxes(gridcolor=t["border"], linecolor=t["border"], zeroline=False)
    fig.update_yaxes(gridcolor=t["border"], linecolor=t["border"], zeroline=False)
    return fig


def _layout(**overrides):
    layout = copy.deepcopy(PLOTLY_LAYOUT)
    layout.update(overrides)
    return layout


def _apply_axes(fig, x_title=None, y_title=None, y_currency=False, x_currency=False):
    """Apply axis titles and optional currency formatting to a Plotly figure."""
    if x_title is not None:
        fig.update_xaxes(title_text=x_title)
    if y_title is not None:
        fig.update_yaxes(title_text=y_title)
    if y_currency:
        fig.update_yaxes(tickformat=PHP_TICK_FORMAT, tickprefix=PHP_TICK_PREFIX)
    if x_currency:
        fig.update_xaxes(tickformat=PHP_TICK_FORMAT, tickprefix=PHP_TICK_PREFIX)
    return fig


def bar_chart(df, x, y, color=None, color_map=None, orientation="v", barmode="group",
              height=320, x_title=None, y_title=None, y_currency=True, label_map=None,
              category_orders=None):
    if label_map:
        df = df.copy()
        for col in (x, y, color):
            if col and col in df.columns and df[col].dtype == object:
                df[col] = df[col].map(lambda v: label_map.get(v, v))
    px_kwargs = {"orientation": orientation}
    if category_orders:
        px_kwargs["category_orders"] = category_orders
    if color and color_map:
        fig = px.bar(df, x=x, y=y, color=color, color_discrete_map=color_map,
                     barmode=barmode, **px_kwargs)
    elif color:
        fig = px.bar(df, x=x, y=y, color=color, color_discrete_sequence=CHART_COLORS,
                     barmode=barmode, **px_kwargs)
    else:
        fig = px.bar(df, x=x, y=y, color_discrete_sequence=CHART_COLORS, **px_kwargs)
    fig.update_layout(**_layout(height=height))
    fig.update_traces(
        marker=dict(cornerradius=6),
        hovertemplate="<b>%{x}</b><br>" + PHP_SYMBOL + "%{y:,.0f}<extra></extra>" if orientation == "v"
        else "<b>%{y}</b><br>" + PHP_SYMBOL + "%{x:,.0f}<extra></extra>",
    )
    if orientation == "v":
        _apply_axes(fig, x_title=x_title, y_title=y_title, y_currency=y_currency)
    else:
        _apply_axes(fig, x_title=x_title, y_title=y_title, x_currency=y_currency)
    return apply_theme(fig)


def horizontal_bar(df, x, y, color_seq=None, height=None, x_title=None, y_title=None,
                   x_currency=True, show_values=False, dynamic_height=True, label_map=None):
    if label_map:
        df = df.copy()
        if y in df.columns and df[y].dtype == object:
            df[y] = df[y].map(lambda v: label_map.get(v, v))
    colors = color_seq or [CHART_COLORS[0]]
    if height is None and dynamic_height:
        n = len(df)
        height = max(240, min(520, 38 * n + 60))
    elif height is None:
        height = 320

    fig = px.bar(df, x=x, y=y, orientation="h", color_discrete_sequence=colors)
    fig.update_layout(**_layout(height=height))
    fig.update_yaxes(autorange="reversed")

    trace_kwargs = dict(
        marker=dict(cornerradius=6),
        hovertemplate="<b>%{y}</b><br>" + PHP_SYMBOL + "%{x:,.0f}<extra></extra>",
    )
    if show_values:
        trace_kwargs["texttemplate"] = PHP_SYMBOL + "%{x:,.3s}"
        trace_kwargs["textposition"] = "outside"
        trace_kwargs["textfont"] = dict(color=TEXT_SECONDARY, size=10)
        trace_kwargs["cliponaxis"] = False
    fig.update_traces(**trace_kwargs)
    _apply_axes(fig, x_title=x_title, y_title=y_title, x_currency=x_currency)
    return apply_theme(fig)


def donut_chart(labels, values, colors=None, height=300, center_text=None,
                label_map=None, value_is_currency=True, unit_label=""):
    """Donut chart.

    value_is_currency: when False, hover shows raw count instead of ₱ prefix.
    unit_label: optional suffix appended after the count (e.g. "customers").
    """
    if label_map:
        labels = [label_map.get(l, l) for l in labels]
    n = len(labels)
    total = sum(values) if values else 1
    text_positions = ["inside" if (v / total) >= 0.08 else "outside" for v in values] if total > 0 else ["outside"] * n

    if value_is_currency:
        hover = "<b>%{label}</b><br>" + PHP_SYMBOL + "%{value:,.0f}<br>%{percent}<extra></extra>"
    else:
        suffix = (" " + unit_label) if unit_label else ""
        hover = "<b>%{label}</b><br>%{value:,.0f}" + suffix + "<br>%{percent}<extra></extra>"

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.65,
        marker=dict(colors=colors or CHART_COLORS, line=dict(color=BG_CARD, width=2)),
        textinfo="percent",
        textposition=text_positions,
        textfont=dict(size=11, color="#FFFFFF"),
        insidetextorientation="radial",
        hovertemplate=hover,
        pull=[0.015] * n,
        sort=False,
    ))
    if center_text:
        # Neutral dark — renders on both light and dark card backgrounds.
        fig.add_annotation(text=f"<b>{center_text}</b>", x=0.5, y=0.5,
                           font=dict(size=22, color="#222222", family="Inter"),
                           showarrow=False, xref="paper", yref="paper")

    # Legend side for 4+ segments, top for fewer
    if n >= 4:
        legend = dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02,
                      font=dict(size=11, color=TEXT_SECONDARY))
    else:
        legend = dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
                      font=dict(size=11, color=TEXT_SECONDARY))

    fig.update_layout(**_layout(height=height, showlegend=True, legend=legend,
                                margin=dict(l=10, r=10, t=20, b=20)))
    return apply_theme(fig)


def line_bar_combo(df, x, bar_y, line_y, bar_name="", line_name="", height=320,
                   x_title=None, y_title=None, y_currency=True,
                   line_on_secondary=False, line_y_title=None, line_currency=True):
    """Bar + line combo chart. Defaults assume bar and line share the same
    unit (e.g. PHP vs PHP). Opt into `line_on_secondary=True` with
    `line_currency=False` when the line is a count or other non-currency
    series that would otherwise get squashed against a currency bar's scale."""
    fig = go.Figure()
    bar_tpl = ("<b>%{x}</b><br>" + bar_name + ": "
               + (PHP_SYMBOL if y_currency else "") + "%{y:,.0f}<extra></extra>")
    line_tpl = ("<b>%{x}</b><br>" + line_name + ": "
                + (PHP_SYMBOL if line_currency else "") + "%{y:,.0f}<extra></extra>")

    fig.add_trace(go.Bar(
        x=df[x], y=df[bar_y], name=bar_name,
        marker=dict(color=CHART_COLORS[0], cornerradius=6),
        opacity=0.85,
        hovertemplate=bar_tpl,
    ))
    fig.add_trace(go.Scatter(
        x=df[x], y=df[line_y], name=line_name,
        mode="lines+markers",
        line=dict(color=CHART_COLORS[2], width=2.5, shape="spline"),
        marker=dict(size=7, color=CHART_COLORS[2], line=dict(width=2, color=BG_CARD)),
        hovertemplate=line_tpl,
        yaxis="y2" if line_on_secondary else "y",
    ))
    fig.update_layout(**_layout(height=height, barmode="overlay"))
    _apply_axes(fig, x_title=x_title, y_title=y_title, y_currency=y_currency)
    if line_on_secondary:
        fig.update_layout(yaxis2=dict(
            title=dict(text=line_y_title or line_name, font=dict(color=CHART_COLORS[2])),
            overlaying="y", side="right", showgrid=False,
            tickfont=dict(color=CHART_COLORS[2]),
            tickformat=(PHP_TICK_FORMAT if line_currency else ",d"),
            tickprefix=(PHP_TICK_PREFIX if line_currency else ""),
        ))
    return apply_theme(fig)


def stacked_bar(df, x, y, color, color_map=None, height=320,
                x_title=None, y_title=None, y_currency=True, label_map=None):
    if label_map:
        df = df.copy()
        for col in (x, color):
            if col in df.columns and df[col].dtype == object:
                df[col] = df[col].map(lambda v: label_map.get(v, v))
    fig = px.bar(df, x=x, y=y, color=color,
                 color_discrete_map=color_map, color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**_layout(height=height, barmode="stack"))
    fig.update_traces(
        marker=dict(cornerradius=4),
        hovertemplate="<b>%{x}</b><br>%{fullData.name}: " + PHP_SYMBOL + "%{y:,.0f}<extra></extra>",
    )
    _apply_axes(fig, x_title=x_title, y_title=y_title, y_currency=y_currency)
    return apply_theme(fig)


def area_chart(df, x, y_cols, colors=None, height=320,
               x_title=None, y_title=None, y_currency=False):
    fig = go.Figure()
    palette = colors or CHART_COLORS
    for i, col in enumerate(y_cols):
        base_color = palette[i % len(palette)]
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], name=col,
            mode="lines", fill="tonexty" if i > 0 else "tozeroy",
            line=dict(width=1.5, color=base_color, shape="spline"),
            fillcolor=base_color,
            hovertemplate="<b>%{x}</b><br>" + col + ": %{y:,.1f}<extra></extra>",
        ))
    fig.update_layout(**_layout(height=height))
    _apply_axes(fig, x_title=x_title, y_title=y_title, y_currency=y_currency)
    return apply_theme(fig)


def treemap_chart(df, path, values, color=None, height=400):
    fig = px.treemap(df, path=path, values=values, color=color,
                     color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**_layout(height=height, margin=dict(l=5, r=5, t=5, b=5)))
    fig.update_traces(
        textfont=dict(color="#FFFFFF", size=12),
        hovertemplate="<b>%{label}</b><br>" + PHP_SYMBOL + "%{value:,.0f}<br>%{percentParent:.1%} of parent<extra></extra>",
        marker=dict(cornerradius=4),
    )
    return apply_theme(fig)


def funnel_chart(stages, values, height=300):
    fig = go.Figure(go.Funnel(
        y=stages, x=values,
        textinfo="value+percent initial",
        texttemplate=PHP_SYMBOL + "%{value:,.0f}<br>%{percentInitial}",
        textfont=dict(color=TEXT_PRIMARY),
        marker=dict(color=CHART_COLORS[:len(stages)]),
        connector=dict(line=dict(color=BORDER, width=1)),
        hovertemplate="<b>%{y}</b><br>" + PHP_SYMBOL + "%{x:,.0f}<br>%{percentInitial} of booked<extra></extra>",
    ))
    fig.update_layout(**_layout(height=height))
    return apply_theme(fig)


def histogram_chart(df, x, nbins=30, height=320, x_title=None, y_title="Count"):
    fig = px.histogram(df, x=x, nbins=nbins, color_discrete_sequence=[CHART_COLORS[0]])
    fig.update_layout(**_layout(height=height))
    fig.update_traces(marker=dict(cornerradius=3, line=dict(width=0)))
    _apply_axes(fig, x_title=x_title, y_title=y_title)
    return fig


def box_chart(df, x, y, height=320, x_title=None, y_title=None):
    fig = px.box(df, x=x, y=y, color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**_layout(height=height))
    _apply_axes(fig, x_title=x_title, y_title=y_title)
    return fig


AGING_BUCKET_COLORS = {
    "0-30d":   "#00D68F",
    "31-60d":  "#E2B04A",
    "61-90d":  "#D39B3C",
    "91-180d": "#F26D6D",
    "180+d":   "#9E3636",
}


def color_by_aging_bucket(client_order, aging_per_client, palette=None):
    """Return a list of colors aligned to client_order, picked by each client's
    dominant aging bucket. `aging_per_client` is a dict {client: bucket_label}.
    Unknown clients fall back to the 0-30d color.
    """
    pal = palette or AGING_BUCKET_COLORS
    fallback = pal.get("0-30d", "#00D68F")
    return [pal.get(aging_per_client.get(c), fallback) for c in client_order]


def add_target_line(fig, target_value, label="Target", color="#F26D6D"):
    """Add a horizontal dashed target line to a chart."""
    fig.add_hline(
        y=target_value,
        line_dash="dash",
        line_color=color,
        line_width=1.5,
        opacity=0.7,
        annotation_text=label,
        annotation_position="top right",
        annotation_font=dict(size=10, color=color, family="Inter"),
    )
    return fig


def enrich_chart_data(df, value_col, label_col=None):
    """Add rank, share %, and vs-average columns for richer hover."""
    df = df.copy()
    total = df[value_col].sum()
    df["_share_pct"] = (df[value_col] / total * 100) if total > 0 else 0
    df["_rank"] = df[value_col].rank(ascending=False, method="min").astype(int)
    df["_vs_avg"] = df[value_col] - df[value_col].mean()
    return df


def gauge_chart(value, max_val=100, height=200, target=None):
    if value >= 75:
        color = "#00D68F"
    elif value >= 50:
        color = "#E2B04A"
    else:
        color = "#F26D6D"

    indicator_kwargs = dict(
        mode="gauge+number",
        value=value,
        number=dict(suffix="%", font=dict(color=TEXT_PRIMARY, size=28)),
        gauge=dict(
            axis=dict(range=[0, max_val], tickfont=dict(color=TEXT_SECONDARY, size=10)),
            bar=dict(color=color, thickness=0.3),
            bgcolor=BG_CARD,
            bordercolor=BORDER,
            steps=[
                dict(range=[0, 50],   color="rgba(242,109,109,0.10)"),
                dict(range=[50, 75],  color="rgba(226,176,74,0.10)"),
                dict(range=[75, 100], color="rgba(0,214,143,0.10)"),
            ],
        ),
    )
    if target is not None:
        indicator_kwargs["gauge"]["threshold"] = dict(
            line=dict(color="#F4F5F6", width=2),
            thickness=0.8,
            value=target,
        )
        indicator_kwargs["mode"] = "gauge+number+delta"
        indicator_kwargs["delta"] = dict(reference=target, increasing=dict(color="#00D68F"),
                                          decreasing=dict(color="#F26D6D"),
                                          font=dict(size=12))

    fig = go.Figure(go.Indicator(**indicator_kwargs))
    fig.update_layout(**_layout(height=height, margin=dict(l=20, r=20, t=20, b=5)))
    return fig
