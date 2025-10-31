"""
SynthAIx Streamlit Frontend - Main Application
Human-in-the-Loop control center for synthetic data generation.
"""

import streamlit as st
import time
import json
from datetime import datetime
from typing import Dict, Any
import pandas as pd

from utils.api_client import APIClient
from components.visualizations import (
    create_progress_bar,
    create_chunk_progress_chart,
    create_metrics_cards,
    create_speed_gauge,
    create_time_estimate_chart
)

# Page configuration
st.set_page_config(
    page_title="SynthAIx - Synthetic Data Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "api_client" not in st.session_state:
    st.session_state.api_client = APIClient()

if "current_step" not in st.session_state:
    st.session_state.current_step = 1

if "schema" not in st.session_state:
    st.session_state.schema = None

if "job_id" not in st.session_state:
    st.session_state.job_id = None

if "prompt" not in st.session_state:
    st.session_state.prompt = ""


def main():
    """Main application entry point."""
    
    # Header
    st.markdown('<div class="main-header">🤖 SynthAIx</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">The Scalable Synthetic Data Generator</div>',
        unsafe_allow_html=True
    )
    
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        
        # Check backend health (with cache to avoid hammering)
        if 'last_health_check' not in st.session_state or \
           (time.time() - st.session_state.last_health_check) > 30:
            try:
                health = st.session_state.api_client.health_check()
                st.session_state.backend_healthy = True
                st.session_state.last_health_check = time.time()
                st.success(f"✅ Backend: {health.get('status', 'unknown').upper()}")
            except Exception as e:
                st.session_state.backend_healthy = False
                st.warning(f"⚠️ Backend: {str(e)}")
                st.info("Backend may be busy generating data. Try refreshing.")
        else:
            # Use cached status
            if st.session_state.get('backend_healthy', False):
                st.success("✅ Backend: HEALTHY (cached)")
            else:
                st.warning("⚠️ Backend status unknown")
        
        st.divider()
        
        # Step indicator
        st.subheader("Process Steps")
        steps = [
            "1️⃣ Schema Input",
            "2️⃣ Schema Confirmation",
            "3️⃣ Data Generation",
            "4️⃣ Results & Download"
        ]
        
        for i, step in enumerate(steps, 1):
            if i < st.session_state.current_step:
                st.success(step)
            elif i == st.session_state.current_step:
                st.info(f"**{step}** ← Current")
            else:
                st.text(step)
        
        st.divider()
        
        # Reset button
        if st.button("🔄 Start New Generation", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key != "api_client":
                    del st.session_state[key]
            st.session_state.current_step = 1
            st.rerun()
    
    # Main content based on current step
    if st.session_state.current_step == 1:
        schema_input_step()
    elif st.session_state.current_step == 2:
        schema_confirmation_step()
    elif st.session_state.current_step == 3:
        data_generation_step()
    elif st.session_state.current_step == 4:
        results_step()


def schema_input_step():
    """Step 1: Natural language schema input."""
    
    st.header("Step 1: Describe Your Data")
    
    st.markdown("""
    <div class="info-box">
    <strong>💡 How it works:</strong><br>
    Describe the data you want in natural language. Our AI will convert it to a structured schema.
    </div>
    """, unsafe_allow_html=True)
    
    # Example prompts
    with st.expander("📝 Example Prompts"):
        st.code("""
1. "Generate financial transactions with date, amount, merchant name, category, and user ID"

2. "Create customer records with name, email, phone, address, registration date, and account balance"

3. "Generate IoT sensor data with timestamp, device ID, temperature, humidity, and battery level"

4. "Create e-commerce orders with order ID, product name, quantity, price, customer email, and shipping address"
        """)
    
    # Input area
    prompt = st.text_area(
        "Describe your data:",
        value=st.session_state.prompt,
        height=150,
        placeholder="E.g., Generate financial transactions with transaction ID, date, amount, merchant name, and category..."
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("🚀 Generate Schema", use_container_width=True, type="primary"):
            if not prompt.strip():
                st.error("Please enter a description of your data.")
                return
            
            with st.spinner("🤖 AI is inferring your schema..."):
                try:
                    response = st.session_state.api_client.translate_schema(prompt)
                    st.session_state.schema = response["schema"]
                    st.session_state.prompt = prompt
                    st.session_state.interpretation = response.get("interpretation", "")
                    st.session_state.confidence = response.get("confidence", 0.0)
                    st.session_state.current_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Schema generation failed: {str(e)}")


def schema_confirmation_step():
    """Step 2: Human-in-the-loop schema confirmation."""
    
    st.header("Step 2: Confirm Your Schema")
    
    st.markdown(f"""
    <div class="info-box">
    <strong>🎯 AI Interpretation:</strong><br>
    {st.session_state.interpretation}
    <br><br>
    <strong>Confidence Score:</strong> {st.session_state.confidence*100:.1f}%
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📋 Schema Definition")
    
    # Display schema in editable format
    schema_data = st.session_state.schema
    
    # Show fields as a dataframe
    if "fields" in schema_data:
        fields_df = pd.DataFrame(schema_data["fields"])
        
        st.markdown("""
        <div class="warning-box">
        <strong>⚠️ Human-in-the-Loop Checkpoint:</strong><br>
        Review the schema below. This ensures 100% accuracy before generation starts.
        Edit the JSON below if needed.
        </div>
        """, unsafe_allow_html=True)
        
        # Display as table
        st.dataframe(fields_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Editable JSON
        st.subheader("🔧 Advanced: Edit JSON Schema")
        edited_schema = st.text_area(
            "Schema JSON:",
            value=json.dumps(schema_data, indent=2),
            height=300
        )
        
        # Generation parameters
        st.divider()
        st.subheader("⚙️ Generation Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_rows = st.number_input(
                "Total Rows",
                min_value=10,
                max_value=1000000,
                value=100,  # Changed from 10000 to 100 for quick demo
                step=10,
                help="Total number of rows to generate"
            )
        
        with col2:
            chunk_size = st.number_input(
                "Chunk Size (optional)",
                min_value=5,
                max_value=100,
                value=50,
                step=5,
                help="Rows per parallel chunk. With MCP+Copilot, we can handle 1000s of chunks!"
            )
        
        with col3:
            enable_dedup = st.checkbox(
                "Enable Deduplication",
                value=False,
                help="Use vector-based duplicate detection (slower)"
            )
        
        # Show parallelization info
        num_chunks = (total_rows + chunk_size - 1) // chunk_size
        st.info(f"""
        **🚀 Parallelization with Unlimited Copilot Tokens:**
        - **{num_chunks:,} chunks** will be processed simultaneously
        - **No rate limits!** All chunks run in parallel
        - **Estimated time:** {(num_chunks * 2) / 60:.1f} minutes with MCP
        """)
        
        if num_chunks > 1000:
            st.warning(f"⚡ **SUPERCHARGED MODE**: {num_chunks:,} parallel chunks! This would be impossible with API rate limits.")
        elif num_chunks > 500:
            st.success(f"🔥 **HIGH PERFORMANCE**: {num_chunks:,} parallel chunks running!")
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.current_step = 1
                st.rerun()
        
        with col3:
            if st.button("✅ Confirm & Generate", use_container_width=True, type="primary"):
                try:
                    # Parse edited schema
                    schema_data = json.loads(edited_schema)
                    
                    # Start generation
                    with st.spinner("🚀 Starting data generation..."):
                        response = st.session_state.api_client.generate_data(
                            schema=schema_data,
                            total_rows=total_rows,
                            chunk_size=chunk_size if chunk_size > 0 else None,
                            enable_deduplication=enable_dedup
                        )
                        
                        st.session_state.job_id = response["job_id"]
                        st.session_state.total_rows = total_rows
                        st.session_state.start_time = time.time()
                        st.session_state.current_step = 3
                        st.rerun()
                
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format. Please check your schema.")
                except Exception as e:
                    st.error(f"❌ Failed to start generation: {str(e)}")


def data_generation_step():
    """Step 3: Live progress tracking and monitoring with enhanced visualizations."""
    
    st.header("🚀 Step 3: Real-Time Data Generation")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Live Progress", "⚡ Performance", "🔍 Chunk Details", "📈 Metrics Over Time"])
    
    # Polling for status updates
    status_placeholder = st.empty()
    
    with status_placeholder.container():
        try:
            status = st.session_state.api_client.get_job_status(st.session_state.job_id)
            
            # Calculate real-time metrics
            elapsed_time = time.time() - st.session_state.start_time
            completed_rows = status.get("completed_rows", 0)
            total_rows = status.get("total_rows", 1)
            progress_pct = status.get("progress_percentage", 0)
            
            # Speed calculation
            speed = completed_rows / elapsed_time if elapsed_time > 0 else 0
            estimated_remaining = (total_rows - completed_rows) / speed if speed > 0 else 0
            
            # Store history for time-series chart
            if 'progress_history' not in st.session_state:
                st.session_state.progress_history = []
            st.session_state.progress_history.append({
                'time': elapsed_time,
                'rows': completed_rows,
                'progress': progress_pct
            })
            
            # Main progress section with animations
            with tab1:
                # Big animated progress indicator
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 20px; color: white;">
                    <h1 style="margin: 0; font-size: 4rem; animation: pulse 2s infinite;">{progress_pct:.1f}%</h1>
                    <p style="margin: 5px 0; font-size: 1.2rem;">Generation Progress</p>
                    <p style="margin: 0; font-size: 0.9rem; opacity: 0.8;">{completed_rows:,} / {total_rows:,} rows completed</p>
                </div>
                <style>
                @keyframes pulse {{
                    0%, 100% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.05); }}
                }}
                </style>
                """, unsafe_allow_html=True)
                
                # Real-time metrics in colored cards
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div style="background: #4CAF50; padding: 20px; border-radius: 10px; text-align: center; color: white;">
                        <h3 style="margin: 0;">⏱️ {elapsed_time:.1f}s</h3>
                        <p style="margin: 5px 0; opacity: 0.9;">Time Elapsed</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="background: #2196F3; padding: 20px; border-radius: 10px; text-align: center; color: white;">
                        <h3 style="margin: 0;">🕐 {estimated_remaining:.1f}s</h3>
                        <p style="margin: 5px 0; opacity: 0.9;">Est. Remaining</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="background: #FF9800; padding: 20px; border-radius: 10px; text-align: center; color: white;">
                        <h3 style="margin: 0;">⚡ {speed:.1f}</h3>
                        <p style="margin: 5px 0; opacity: 0.9;">Rows/Second</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    tokens = status.get("metrics", {}).get("tokens_used", 0)
                    st.markdown(f"""
                    <div style="background: #9C27B0; padding: 20px; border-radius: 10px; text-align: center; color: white;">
                        <h3 style="margin: 0;">🎫 {tokens:,}</h3>
                        <p style="margin: 5px 0; opacity: 0.9;">Tokens Used</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Animated progress bar
                st.plotly_chart(
                    create_progress_bar(
                        progress_pct,
                        total_rows,
                        completed_rows
                    ),
                    use_container_width=True
                )
                
                # Status indicator with emoji
                status_map = {
                    "pending": ("🟡", "Pending", "#FFC107"),
                    "in_progress": ("🔵", "In Progress", "#2196F3"),
                    "completed": ("🟢", "Completed", "#4CAF50"),
                    "failed": ("🔴", "Failed", "#F44336")
                }
                emoji, text, color = status_map.get(status['status'], ("⚪", "Unknown", "#999"))
                
                st.markdown(f"""
                <div style="background: {color}20; border-left: 4px solid {color}; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong style="font-size: 1.1rem;">{emoji} Status:</strong> <span style="font-size: 1.1rem;">{text}</span><br>
                    <small style="opacity: 0.7;">Job ID: {st.session_state.job_id}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Chunk progress visualization
                if status.get("chunks"):
                    st.subheader("📦 Chunk Progress")
                    st.plotly_chart(
                        create_chunk_progress_chart(status["chunks"]),
                        use_container_width=True
                    )
            
            # Performance tab with enhanced metrics
            with tab2:
                metrics = status.get("metrics", {})
                
                st.subheader("⚡ Real-Time Performance Metrics")
                
                # Performance metrics in grid
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "🎯 API Calls Made",
                        f"{metrics.get('api_calls', 0)}",
                        delta=f"+{metrics.get('api_calls', 0)} total"
                    )
                    st.metric(
                        "⏱️ Avg Response Time",
                        f"{metrics.get('avg_response_time', 0):.2f}s",
                        delta=None
                    )
                    st.metric(
                        "🔄 Duplicates Removed",
                        f"{metrics.get('total_duplicates_removed', 0)}",
                        delta=None
                    )
                
                with col2:
                    completed_chunks = status.get("completed_chunks", 0)
                    total_chunks = status.get("total_chunks", 1)
                    st.metric(
                        "📦 Chunks Completed",
                        f"{completed_chunks}/{total_chunks}",
                        delta=f"{(completed_chunks/total_chunks*100):.0f}%"
                    )
                    
                    # Token efficiency
                    tokens_per_row = tokens / completed_rows if completed_rows > 0 else 0
                    st.metric(
                        "💰 Tokens per Row",
                        f"{tokens_per_row:.1f}",
                        delta=None
                    )
                    
                    # Rows per minute
                    rpm = (completed_rows / elapsed_time * 60) if elapsed_time > 0 else 0
                    st.metric(
                        "📊 Rows per Minute",
                        f"{rpm:.0f}",
                        delta=None
                    )
                
                st.divider()
                
                # Speed gauge
                st.subheader("🏎️ Generation Speed")
                st.plotly_chart(
                    create_speed_gauge(speed),
                    use_container_width=True
                )
            
            # Chunk details tab
            with tab3:
                if status.get("chunks"):
                    st.subheader("🔍 Detailed Chunk Information")
                    chunks_df = pd.DataFrame(status["chunks"])
                    
                    # Add status emoji
                    if 'status' in chunks_df.columns:
                        chunks_df['status'] = chunks_df['status'].map({
                            'completed': '✅ Completed',
                            'pending': '⏳ Pending',
                            'in_progress': '🔄 In Progress',
                            'failed': '❌ Failed'
                        })
                    
                    st.dataframe(
                        chunks_df,
                        use_container_width=True,
                        hide_index=True
                    )
            
            # Time series metrics tab
            with tab4:
                if len(st.session_state.progress_history) > 1:
                    st.subheader("📈 Progress Over Time")
                    
                    history_df = pd.DataFrame(st.session_state.progress_history)
                    
                    # Line chart for progress
                    import plotly.graph_objects as go
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=history_df['time'],
                        y=history_df['rows'],
                        mode='lines+markers',
                        name='Rows Generated',
                        line=dict(color='#2196F3', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(33, 150, 243, 0.2)'
                    ))
                    
                    fig.update_layout(
                        title="Rows Generated Over Time",
                        xaxis_title="Time (seconds)",
                        yaxis_title="Total Rows",
                        hovermode='x unified',
                        template='plotly_white',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Progress percentage chart
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(
                        x=history_df['time'],
                        y=history_df['progress'],
                        mode='lines+markers',
                        name='Progress %',
                        line=dict(color='#4CAF50', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(76, 175, 80, 0.2)'
                    ))
                    
                    fig2.update_layout(
                        title="Progress Percentage Over Time",
                        xaxis_title="Time (seconds)",
                        yaxis_title="Progress (%)",
                        hovermode='x unified',
                        template='plotly_white',
                        height=400
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("⏳ Gathering data... Charts will appear as generation progresses.")
            
            # Check if completed
            if status["status"] == "completed":
                st.balloons()
                st.success("✅ Data generation completed successfully!")
                st.session_state.current_step = 4
                time.sleep(2)
                st.rerun()
            elif status["status"] == "failed":
                st.error(f"❌ Generation failed: {status.get('error', 'Unknown error')}")
                if st.button("🔄 Start Over"):
                    st.session_state.current_step = 1
                    st.rerun()
            else:
                # Auto-refresh with optimized interval
                time.sleep(3)  # Poll every 3 seconds for smooth updates
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error fetching status: {str(e)}")
            st.info("💡 Tip: Backend may be busy. Wait a moment and click Retry.")
            if st.button("🔄 Retry"):
                st.rerun()


def results_step():
    """Step 4: Display results and download options."""
    
    st.header("Step 4: Your Synthetic Data is Ready! 🎉")
    
    try:
        status = st.session_state.api_client.get_job_status(st.session_state.job_id)
        
        # Success message
        st.markdown(f"""
        <div class="success-box">
        <h3>✅ Generation Complete!</h3>
        <p><strong>Total Rows Generated:</strong> {status['completed_rows']:,}</p>
        <p><strong>Job ID:</strong> {st.session_state.job_id}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Final metrics
        st.subheader("📊 Final Statistics")
        
        metrics = status.get("metrics", {})
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric("Total Tokens", f"{metrics.get('tokens_used', 0):,}")
        col2.metric("API Calls", f"{metrics.get('api_calls', 0):,}")
        col3.metric("Avg Response Time", f"{metrics.get('avg_response_time', 0):.2f}s")
        col4.metric("Dedup Rate", f"{metrics.get('deduplication_rate', 0)*100:.1f}%")
        col5.metric("Duplicates Removed", f"{metrics.get('total_duplicates_removed', 0):,}")
        
        st.divider()
        
        # Data preview
        if status.get("data"):
            st.subheader("📋 Data Preview")
            
            df = pd.DataFrame(status["data"])
            st.dataframe(df.head(100), use_container_width=True)
            
            st.info(f"Showing first 100 rows. Total: {len(df):,} rows")
            
            # Download options
            st.subheader("💾 Download Data")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"synthaix_data_{st.session_state.job_id}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                json_data = df.to_json(orient="records", indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"synthaix_data_{st.session_state.job_id}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col3:
                excel_buffer = df.to_excel(engine='openpyxl', index=False)
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_buffer,
                    file_name=f"synthaix_data_{st.session_state.job_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        # Generate more or start new
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Generate More Data", use_container_width=True):
                st.session_state.current_step = 2
                st.rerun()
        
        with col2:
            if st.button("🆕 Start New Project", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    if key != "api_client":
                        del st.session_state[key]
                st.session_state.current_step = 1
                st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error loading results: {str(e)}")


if __name__ == "__main__":
    main()
