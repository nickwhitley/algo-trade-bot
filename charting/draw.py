import pandas as pd
import datetime as dt
from api.oanda_api import OandaApi
from dateutil import parser
import timeit
import plotly.graph_objects as go

def draw_candlestick_chart(df):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.sTime,
        open=df.mid_o,
        high=df.mid_h,
        low=df.mid_l,
        close=df.mid_c,
        line=dict(width=1), opacity=1,
        increasing_fillcolor='#24A06B', 
        decreasing_fillcolor='#CC2E3C',
        increasing_line_color='#24A06B',
        decreasing_line_color='#FF3A4C'
    ))

    apply_layout(df, fig)

    return fig

def apply_layout(df, fig):
    x_start = df['sTime'].iloc[0]
    x_end = df['sTime'].iloc[-1]
    y_min = df['mid_l'].min()
    y_max = df['mid_h'].max()
    padding = (y_max - y_min) * 0.1

    fig.update_yaxes(
        autorange=True,
        fixedrange=False,
        rangemode='normal',
        scaleratio=1,
        automargin=True,
        gridcolor="#1f292f"
    )

    fig.update_xaxes(
        gridcolor="#1f292f",
        rangeslider=dict(visible=True),
        nticks=5
    )

    fig.update_layout(
        width=1500,
        height=600,
        margin=dict(l=10,r=10,b=10,t=10),
        paper_bgcolor="#2c303c",
        plot_bgcolor="#2c303c",
        font=dict(size=10, color="#e1e1e1")
    )

    fig.update_layout(
        yaxis=dict(
            range=[y_min - padding, y_max + padding],
            fixedrange=False  # Allow zooming
        )
    )

def highlight_downtrend_candles(fig, df, color='blue'):
    df_downtrend = df[df['in_downtrend'] == True]

    fig.add_trace(go.Candlestick(
        x=df_downtrend.sTime,
        open=df_downtrend.mid_o,
        high=df_downtrend.mid_h,
        low=df_downtrend.mid_l,
        close=df_downtrend.mid_c,
        line=dict(width=1), opacity=1,
        increasing_fillcolor=color, 
        decreasing_fillcolor=color,
        increasing_line_color=color,
        decreasing_line_color=color
    ))

def highlight_bottom_zones(fig, df, color='yellow'):
    bottoms = df[df['is_bottom'] == True]

    fig.add_trace(go.Candlestick(
        x=bottoms.sTime,
        open=bottoms.mid_o,
        high=bottoms.mid_h,
        low=bottoms.mid_l,
        close=bottoms.mid_c,
        line=dict(width=1), opacity=1,
        increasing_fillcolor='yellow', 
        decreasing_fillcolor='yellow',
        increasing_line_color='yellow',
        decreasing_line_color='yellow'
    ))

def highlight_exits_and_reentries(fig, df, exit_color='red', reentry_color='green'):
    exits = df[df['setup_stage'] == 'exit']
    reentries = df[df['setup_stage'] == 'reentry']

    # Draw red arrows for exits
    for _, row in exits.iterrows():
        fig.add_annotation(
            x=row['sTime'],
            y=row['mid_h'],
            ax=row['sTime'],
            ay=row['mid_h'] + 0.0015,
            xref='x', yref='y',
            axref='x', ayref='y',
            text='',
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor='red'
        )

    # Draw green arrows for reentries
    for _, row in reentries.iterrows():
        fig.add_annotation(
            x=row['sTime'],
            y=row['mid_l'],
            ax=row['sTime'],
            ay=row['mid_l'] - 0.0015,
            xref='x', yref='y',
            axref='x', ayref='y',
            text='',
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor='green'
        )

def highlight_strong_bullish_candles(fig, df, color='yellow'):
    strong_bullish = df[df['strong_bullish'] == True]

    fig.add_trace(go.Candlestick(
        x=strong_bullish.sTime,
        open=strong_bullish.mid_o,
        high=strong_bullish.mid_h,
        low=strong_bullish.mid_l,
        close=strong_bullish.mid_c,
        line=dict(width=1), opacity=1,
        increasing_fillcolor=color, 
        decreasing_fillcolor=color,
        increasing_line_color=color,
        decreasing_line_color=color
    ))