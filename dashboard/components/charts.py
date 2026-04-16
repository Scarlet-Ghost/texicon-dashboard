import plotly.graph_objects as go
import plotly.express as px
import copy
from data.constants import CHART_COLORS, PHP_SYMBOL, PLOTLY_LAYOUT, BG_CARD, BORDER, TEXT_PRIMARY, TEXT_SECONDARY


def _layout(**overrides):
    layout = copy.deepcopy(PLOTLY_LAYOUT)
    layout.update(overrides)
    return layout


def bar_chart(df, x, y, color=None, color_map=None, orientation="v", barmode="group", height=320):
    if color and color_map:
        fig = px.bar(df, x=x, y=y, color=color, color_discrete_map=color_map,
                     orientation=orientation, barmode=barmode)
    elif color:
        fig = px.bar(df, x=x, y=y, color=color, color_discrete_sequence=CHART_COLORS,
                     orientation=orientation, barmode=barmode)
    else:
        fig = px.bar(df, x=x, y=y, orientation=orientation,
                     color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**_layout(height=height))
    fig.update_traces(
        hovertemplate="%{x}: " + PHP_SYMBOL + "%{y:,.0f}<extra></extra>" if orientation == "v"
        else "%{y}: " + PHP_SYMBOL + "%{x:,.0f}<extra></extra>"
    )
    return fig


def horizontal_bar(df, x, y, color_seq=None, height=320):
    colors = color_seq or [CHART_COLORS[0]]
    fig = px.bar(df, x=x, y=y, orientation="h", color_discrete_sequence=colors)
    fig.update_layout(**_layout(height=height))
    fig.update_yaxes(autorange="reversed")
    fig.update_traces(
        hovertemplate="%{y}: " + PHP_SYMBOL + "%{x:,.0f}<extra></extra>",
    )
    return fig


def donut_chart(labels, values, colors=None, height=300, center_text=None):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.6,
        marker=dict(colors=colors or CHART_COLORS, line=dict(color=BG_CARD, width=2)),
        textinfo="percent",
        textposition="outside",
        textfont=dict(size=10, color=TEXT_SECONDARY),
        hovertemplate="%{label}<br>" + PHP_SYMBOL + "%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    if center_text:
        fig.add_annotation(text=center_text, x=0.5, y=0.5, font=dict(size=18, color=TEXT_PRIMARY, family="Inter"),
                           showarrow=False, xref="paper", yref="paper")
    fig.update_layout(**_layout(height=height, showlegend=True,
                                legend=dict(font=dict(size=10, color=TEXT_SECONDARY))))
    return fig


def line_bar_combo(df, x, bar_y, line_y, bar_name="", line_name="", height=320):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df[x], y=df[bar_y], name=bar_name,
        marker_color=CHART_COLORS[0], opacity=0.85,
        hovertemplate="%{x}<br>" + bar_name + ": " + PHP_SYMBOL + "%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df[x], y=df[line_y], name=line_name,
        mode="lines+markers",
        line=dict(color=CHART_COLORS[2], width=2),
        marker=dict(size=5, color=CHART_COLORS[2]),
        hovertemplate="%{x}<br>" + line_name + ": " + PHP_SYMBOL + "%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(**_layout(height=height, barmode="overlay"))
    return fig


def stacked_bar(df, x, y, color, color_map=None, height=320):
    fig = px.bar(df, x=x, y=y, color=color,
                 color_discrete_map=color_map, color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**_layout(height=height, barmode="stack"))
    return fig


def area_chart(df, x, y_cols, colors=None, height=320):
    fig = go.Figure()
    palette = colors or CHART_COLORS
    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], name=col,
            mode="lines", fill="tonexty" if i > 0 else "tozeroy",
            line=dict(width=0.5, color=palette[i % len(palette)]),
            fillcolor=palette[i % len(palette)],
            hovertemplate="%{x}<br>" + col + ": " + PHP_SYMBOL + "%{y:,.0f}<extra></extra>",
        ))
    fig.update_layout(**_layout(height=height))
    return fig


def treemap_chart(df, path, values, color=None, height=400):
    fig = px.treemap(df, path=path, values=values, color=color,
                     color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**_layout(height=height, margin=dict(l=5, r=5, t=5, b=5)))
    fig.update_traces(
        textfont=dict(color="#FFFFFF"),
        hovertemplate="%{label}<br>" + PHP_SYMBOL + "%{value:,.0f}<br>%{percentParent:.1%} of parent<extra></extra>",
    )
    return fig


def funnel_chart(stages, values, height=300):
    fig = go.Figure(go.Funnel(
        y=stages, x=values,
        textinfo="value+percent initial",
        texttemplate=PHP_SYMBOL + "%{value:,.0f}<br>%{percentInitial}",
        textfont=dict(color=TEXT_PRIMARY),
        marker=dict(color=CHART_COLORS[:len(stages)]),
        connector=dict(line=dict(color=BORDER, width=1)),
    ))
    fig.update_layout(**_layout(height=height))
    return fig


def histogram_chart(df, x, nbins=30, height=320):
    fig = px.histogram(df, x=x, nbins=nbins, color_discrete_sequence=[CHART_COLORS[0]])
    fig.update_layout(**_layout(height=height))
    return fig


def box_chart(df, x, y, height=320):
    fig = px.box(df, x=x, y=y, color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**_layout(height=height))
    return fig


def gauge_chart(value, max_val=100, height=200):
    if value >= 75:
        color = "#4CAF50"
    elif value >= 50:
        color = "#FFA726"
    else:
        color = "#EF5350"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix="%", font=dict(color=TEXT_PRIMARY, size=28)),
        gauge=dict(
            axis=dict(range=[0, max_val], tickfont=dict(color=TEXT_SECONDARY, size=10)),
            bar=dict(color=color),
            bgcolor=BG_CARD,
            bordercolor=BORDER,
            steps=[
                dict(range=[0, 50], color="rgba(239,83,80,0.1)"),
                dict(range=[50, 75], color="rgba(255,167,38,0.1)"),
                dict(range=[75, 100], color="rgba(76,175,80,0.1)"),
            ],
        ),
    ))
    fig.update_layout(**_layout(height=height))
    return fig
