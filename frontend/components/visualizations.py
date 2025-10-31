"""
Visualization components for the dashboard.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
import pandas as pd


def create_progress_bar(progress: float, total_rows: int, completed_rows: int) -> go.Figure:
    """
    Create an animated progress bar.
    
    Args:
        progress: Progress percentage (0-100)
        total_rows: Total rows to generate
        completed_rows: Rows completed
        
    Returns:
        Plotly figure
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=progress,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Progress<br><sub>{completed_rows:,} / {total_rows:,} rows</sub>"},
        delta={'reference': 0},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


def create_chunk_progress_chart(chunks: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a chart showing chunk completion status.
    
    Args:
        chunks: List of chunk progress data
        
    Returns:
        Plotly figure
    """
    # Prepare data
    chunk_ids = [c["chunk_id"] for c in chunks]
    statuses = [c["status"] for c in chunks]
    rows_generated = [c["rows_generated"] for c in chunks]
    
    # Color mapping
    color_map = {
        "completed": "green",
        "in_progress": "yellow",
        "pending": "lightgray",
        "failed": "red"
    }
    colors = [color_map.get(s, "gray") for s in statuses]
    
    fig = go.Figure(data=[
        go.Bar(
            x=chunk_ids,
            y=rows_generated,
            marker_color=colors,
            text=rows_generated,
            textposition='auto',
            hovertemplate='<b>Chunk %{x}</b><br>Rows: %{y}<br>Status: %{customdata}<extra></extra>',
            customdata=statuses
        )
    ])
    
    fig.update_layout(
        title="Chunk Progress (Parallel Execution)",
        xaxis_title="Chunk ID",
        yaxis_title="Rows Generated",
        height=400,
        showlegend=False
    )
    
    return fig


def create_metrics_cards(metrics: Dict[str, Any]) -> pd.DataFrame:
    """
    Create metrics data for display cards.
    
    Args:
        metrics: Metrics dictionary
        
    Returns:
        DataFrame for metrics display
    """
    return pd.DataFrame([
        {
            "Metric": "Tokens Used",
            "Value": f"{metrics.get('tokens_used', 0):,}",
            "Icon": "🎯"
        },
        {
            "Metric": "API Calls",
            "Value": f"{metrics.get('api_calls', 0):,}",
            "Icon": "📡"
        },
        {
            "Metric": "Avg Response Time",
            "Value": f"{metrics.get('avg_response_time', 0):.2f}s",
            "Icon": "⚡"
        },
        {
            "Metric": "Deduplication Rate",
            "Value": f"{metrics.get('deduplication_rate', 0)*100:.1f}%",
            "Icon": "🔍"
        },
        {
            "Metric": "Duplicates Removed",
            "Value": f"{metrics.get('total_duplicates_removed', 0):,}",
            "Icon": "🗑️"
        }
    ])


def create_speed_gauge(rows_per_second: float) -> go.Figure:
    """
    Create a gauge showing generation speed.
    
    Args:
        rows_per_second: Current generation speed
        
    Returns:
        Plotly figure
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=rows_per_second,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Generation Speed<br><sub>rows/second</sub>"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkgreen"},
            'steps': [
                {'range': [0, 30], 'color': "lightgray"},
                {'range': [30, 60], 'color': "yellow"},
                {'range': [60, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "green", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig


def create_time_estimate_chart(
    elapsed_time: float,
    estimated_remaining: float
) -> go.Figure:
    """
    Create a chart showing time elapsed vs estimated remaining.
    
    Args:
        elapsed_time: Time elapsed in seconds
        estimated_remaining: Estimated time remaining in seconds
        
    Returns:
        Plotly figure
    """
    fig = go.Figure(data=[
        go.Bar(
            x=['Elapsed', 'Remaining'],
            y=[elapsed_time / 60, estimated_remaining / 60],  # Convert to minutes
            marker_color=['blue', 'orange'],
            text=[f"{elapsed_time/60:.1f}m", f"{estimated_remaining/60:.1f}m"],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Time Analysis",
        yaxis_title="Minutes",
        height=300,
        showlegend=False
    )
    
    return fig
