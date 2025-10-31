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
        
        # Check backend health
        try:
            health = st.session_state.api_client.health_check()
            st.success(f"✅ Backend: {health.get('status', 'unknown').upper()}")
        except Exception as e:
            st.error(f"❌ Backend: Offline\n{str(e)}")
            st.stop()
        
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
                value=10000,
                step=100,
                help="Total number of rows to generate"
            )
        
        with col2:
            chunk_size = st.number_input(
                "Chunk Size (optional)",
                min_value=10,
                max_value=1000,
                value=500,
                step=10,
                help="Rows per parallel chunk. Leave default for optimal performance."
            )
        
        with col3:
            enable_dedup = st.checkbox(
                "Enable Deduplication",
                value=True,
                help="Use vector-based duplicate detection"
            )
        
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
    """Step 3: Live progress tracking and monitoring."""
    
    st.header("Step 3: Generating Data")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Progress", "📈 Agent Statistics", "🔍 Chunk Details"])
    
    # Polling for status updates
    status_placeholder = st.empty()
    
    with status_placeholder.container():
        try:
            status = st.session_state.api_client.get_job_status(st.session_state.job_id)
            
            # Main progress section
            with tab1:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Progress bar
                    st.plotly_chart(
                        create_progress_bar(
                            status["progress_percentage"],
                            status["total_rows"],
                            status["completed_rows"]
                        ),
                        use_container_width=True
                    )
                
                with col2:
                    # Time estimates
                    elapsed_time = time.time() - st.session_state.start_time
                    estimated_remaining = status.get("estimated_time_remaining", 0) or 0
                    
                    st.metric("Time Elapsed", f"{elapsed_time:.1f}s")
                    st.metric("Est. Remaining", f"{estimated_remaining:.1f}s")
                    
                    # Speed calculation
                    if elapsed_time > 0:
                        speed = status["completed_rows"] / elapsed_time
                        st.metric("Speed", f"{speed:.1f} rows/s")
                
                # Status indicator
                status_map = {
                    "pending": "🟡 Pending",
                    "in_progress": "🔵 In Progress",
                    "completed": "🟢 Completed",
                    "failed": "🔴 Failed"
                }
                
                st.markdown(f"""
                <div class="info-box">
                <strong>Status:</strong> {status_map.get(status['status'], status['status'])}
                <br><strong>Job ID:</strong> {st.session_state.job_id}
                </div>
                """, unsafe_allow_html=True)
                
                # Chunk progress visualization
                if status.get("chunks"):
                    st.plotly_chart(
                        create_chunk_progress_chart(status["chunks"]),
                        use_container_width=True
                    )
            
            # Agent statistics
            with tab2:
                metrics = status.get("metrics", {})
                
                # Metrics cards
                metrics_df = create_metrics_cards(metrics)
                
                col1, col2, col3 = st.columns(3)
                
                for idx, row in metrics_df.iterrows():
                    col = [col1, col2, col3][idx % 3]
                    with col:
                        st.markdown(f"""
                        <div class="metric-card">
                        <h2 style="margin:0;">{row['Icon']} {row['Value']}</h2>
                        <p style="margin:0; color:#666;">{row['Metric']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.divider()
                
                # Speed gauge
                if elapsed_time > 0:
                    speed = status["completed_rows"] / elapsed_time
                    st.plotly_chart(
                        create_speed_gauge(speed),
                        use_container_width=True
                    )
            
            # Chunk details
            with tab3:
                if status.get("chunks"):
                    chunks_df = pd.DataFrame(status["chunks"])
                    st.dataframe(
                        chunks_df,
                        use_container_width=True,
                        hide_index=True
                    )
            
            # Check if completed
            if status["status"] == "completed":
                st.success("✅ Data generation completed!")
                st.session_state.current_step = 4
                time.sleep(2)
                st.rerun()
            elif status["status"] == "failed":
                st.error(f"❌ Generation failed: {status.get('error', 'Unknown error')}")
                if st.button("🔄 Start Over"):
                    st.session_state.current_step = 1
                    st.rerun()
            else:
                # Auto-refresh
                time.sleep(2)
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error fetching status: {str(e)}")
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
