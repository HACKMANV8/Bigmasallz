"""
SynthAIx Frontend - Streamlit Application
Modern, production-grade UI for synthetic data generation
"""

import streamlit as st
import requests
import pandas as pd
import json
import time
from typing import Optional, Dict, Any
import io

# Configuration
API_BASE_URL = st.secrets.get( "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="SynthAIx - Synthetic Data Generator",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-box {
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        margin: 10px 0;
    }
    .success-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #d4edda;
        border: 2px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f8d7da;
        border: 2px solid #f5c6cb;
        color: #721c24;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'schema' not in st.session_state:
    st.session_state.schema = None
if 'job_id' not in st.session_state:
    st.session_state.job_id = None
if 'job_status' not in st.session_state:
    st.session_state.job_status = None


def api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[Any, Any]:
    """Make API request to backend."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {"error": str(e)}


def translate_schema(description: str) -> Optional[Dict]:
    """Translate natural language to schema."""
    with st.spinner("🤖 AI is analyzing your description..."):
        result = api_request("/api/schema/translate", "POST", {"description": description})
        if "error" not in result:
            return result.get("schema")
    return None


def generate_data(schema: Dict, config: Dict) -> Optional[str]:
    """Start data generation job."""
    with st.spinner("🚀 Starting data generation..."):
        payload = {
            "schema": schema,
            "num_rows": config["num_rows"],
            "chunk_size": config.get("chunk_size", 500),
            "max_workers": config.get("max_workers", 10),
            "enable_deduplication": config.get("enable_deduplication", True),
            "deduplication_threshold": config.get("deduplication_threshold", 0.85)
        }
        result = api_request("/api/data/generate", "POST", payload)
        if "error" not in result:
            return result.get("job_id")
    return None


def get_job_status(job_id: str) -> Optional[Dict]:
    """Get job status."""
    result = api_request(f"/api/jobs/{job_id}/status", "GET")
    if "error" not in result:
        return result
    return None


def download_results(job_id: str, format: str = "csv") -> Optional[bytes]:
    """Download job results."""
    url = f"{API_BASE_URL}/api/jobs/{job_id}/download?format={format}"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"Download Error: {str(e)}")
    return None


def render_header():
    """Render app header."""
    st.markdown('<div class="main-header">🎲 SynthAIx</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Synthetic Data Generator</div>', unsafe_allow_html=True)
    st.markdown("---")


def render_sidebar():
    """Render sidebar with info."""
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=SynthAIx", use_container_width=True)
        st.markdown("## 📊 Features")
        st.markdown("""
        - 🤖 AI-powered schema inference
        - ⚡ Parallel data generation
        - 🎯 Vector-based deduplication
        - 📈 Real-time progress tracking
        - 💾 CSV/JSON export
        """)
        
        st.markdown("## 🔧 Current Step")
        steps = ["📝 Describe", "✏️ Edit Schema", "⚙️ Configure", "🚀 Generate"]
        for i, step_name in enumerate(steps, 1):
            if i == st.session_state.step:
                st.markdown(f"**➡️ {step_name}**")
            elif i < st.session_state.step:
                st.markdown(f"✅ {step_name}")
            else:
                st.markdown(f"⏺️ {step_name}")
        
        st.markdown("---")
        st.markdown("## 📚 Resources")
        st.markdown("[📖 Documentation](https://github.com)")
        st.markdown("[🐛 Report Issue](https://github.com)")
        st.markdown("[💡 Examples](https://github.com)")


def step1_describe():
    """Step 1: Natural language description."""
    st.markdown("### Step 1: Describe Your Dataset")
    st.markdown("Tell the AI what kind of data you want to generate. Be as specific as possible.")
    
    with st.form("description_form"):
        description = st.text_area(
            "Dataset Description",
            placeholder="Example: Customer database with name, email, age, subscription status, and join date",
            height=150,
            help="Describe the columns, data types, and any constraints you need"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit = st.form_submit_button("🤖 Generate Schema", use_container_width=True)
        with col2:
            if st.form_submit_button("📋 Load Example", use_container_width=True):
                st.session_state.example_loaded = True
                st.rerun()
    
    if 'example_loaded' in st.session_state and st.session_state.example_loaded:
        description = "E-commerce product catalog with product name, category, price, stock quantity, description, and rating"
        st.session_state.example_loaded = False
        schema = translate_schema(description)
        if schema:
            st.session_state.schema = schema
            st.session_state.step = 2
            st.rerun()
    
    if submit and description:
        schema = translate_schema(description)
        if schema:
            st.success("✅ Schema generated successfully!")
            st.session_state.schema = schema
            st.session_state.step = 2
            st.rerun()


def step2_edit_schema():
    """Step 2: Edit schema."""
    st.markdown("### Step 2: Review & Edit Schema")
    st.markdown("Review the generated schema and make any necessary adjustments.")
    
    if st.session_state.schema:
        schema = st.session_state.schema
        
        # Display schema info
        st.info(f"**Dataset Name:** {schema.get('name', 'N/A')}  \n**Description:** {schema.get('description', 'N/A')}")
        
        # Edit columns
        st.markdown("#### Columns")
        columns = schema.get("columns", [])
        
        edited_columns = []
        for i, col in enumerate(columns):
            with st.expander(f"📋 {col['name']} ({col['data_type']})", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Column Name", value=col['name'], key=f"name_{i}")
                    data_type = st.selectbox(
                        "Data Type",
                        ["string", "integer", "float", "boolean", "date", "datetime", "email", "phone"],
                        index=["string", "integer", "float", "boolean", "date", "datetime", "email", "phone"].index(col.get('data_type', 'string')),
                        key=f"type_{i}"
                    )
                with col2:
                    description = st.text_area("Description", value=col.get('description', ''), key=f"desc_{i}", height=80)
                
                # Constraints
                constraints = col.get('constraints', {})
                st.markdown("**Constraints:**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    required = st.checkbox("Required", value=constraints.get('required', False), key=f"req_{i}")
                    unique = st.checkbox("Unique", value=constraints.get('unique', False), key=f"uniq_{i}")
                with c2:
                    if data_type in ["integer", "float"]:
                        min_val = st.number_input("Min Value", value=constraints.get('min', 0), key=f"min_{i}")
                        max_val = st.number_input("Max Value", value=constraints.get('max', 100), key=f"max_{i}")
                with c3:
                    if data_type == "string":
                        min_len = st.number_input("Min Length", value=constraints.get('min_length', 1), key=f"minlen_{i}")
                        max_len = st.number_input("Max Length", value=constraints.get('max_length', 100), key=f"maxlen_{i}")
                
                # Build edited column
                edited_col = {
                    "name": name,
                    "data_type": data_type,
                    "description": description,
                    "constraints": {"required": required, "unique": unique}
                }
                if data_type in ["integer", "float"]:
                    edited_col["constraints"]["min"] = min_val
                    edited_col["constraints"]["max"] = max_val
                if data_type == "string":
                    edited_col["constraints"]["min_length"] = min_len
                    edited_col["constraints"]["max_length"] = max_len
                
                edited_columns.append(edited_col)
        
        # Update schema
        st.session_state.schema["columns"] = edited_columns
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
        with col2:
            if st.button("➡️ Next: Configure", use_container_width=True, type="primary"):
                st.session_state.step = 3
                st.rerun()


def step3_configure():
    """Step 3: Configure generation."""
    st.markdown("### Step 3: Configure Generation")
    st.markdown("Set parameters for data generation.")
    
    with st.form("config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            num_rows = st.number_input(
                "Number of Rows",
                min_value=10,
                max_value=1000000,
                value=1000,
                step=100,
                help="Total number of rows to generate"
            )
            chunk_size = st.number_input(
                "Chunk Size",
                min_value=100,
                max_value=2000,
                value=500,
                step=100,
                help="Rows per chunk (for parallel processing)"
            )
            max_workers = st.slider(
                "Parallel Workers",
                min_value=1,
                max_value=50,
                value=10,
                help="Number of parallel workers (more = faster)"
            )
        
        with col2:
            enable_dedup = st.checkbox(
                "Enable Deduplication",
                value=True,
                help="Remove duplicate rows using vector similarity"
            )
            if enable_dedup:
                dedup_threshold = st.slider(
                    "Deduplication Threshold",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.85,
                    step=0.05,
                    help="Higher = more strict (0.85 recommended)"
                )
            else:
                dedup_threshold = 0.0
            
            st.markdown("#### Cost Estimate")
            estimated_cost = (num_rows / 1000) * 0.05  # Rough estimate
            st.metric("Estimated Cost", f"${estimated_cost:.2f}")
            st.caption("Based on GPT-4-Turbo pricing")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            back = st.form_submit_button("⬅️ Back", use_container_width=True)
        with col2:
            submit = st.form_submit_button("🚀 Start Generation", use_container_width=True, type="primary")
    
    if back:
        st.session_state.step = 2
        st.rerun()
    
    if submit:
        config = {
            "num_rows": num_rows,
            "chunk_size": chunk_size,
            "max_workers": max_workers,
            "enable_deduplication": enable_dedup,
            "deduplication_threshold": dedup_threshold
        }
        job_id = generate_data(st.session_state.schema, config)
        if job_id:
            st.success(f"✅ Job started! ID: {job_id}")
            st.session_state.job_id = job_id
            st.session_state.step = 4
            st.rerun()


def step4_generate():
    """Step 4: Generate and track progress."""
    st.markdown("### Step 4: Generating Data")
    
    if not st.session_state.job_id:
        st.error("No job ID found. Please start from Step 1.")
        if st.button("🔄 Start Over"):
            st.session_state.step = 1
            st.session_state.job_id = None
            st.rerun()
        return
    
    job_id = st.session_state.job_id
    
    # Progress tracking
    progress_placeholder = st.empty()
    metrics_placeholder = st.empty()
    logs_placeholder = st.empty()
    
    # Poll for status
    max_polls = 600  # 10 minutes max
    poll_count = 0
    
    while poll_count < max_polls:
        status = get_job_status(job_id)
        
        if not status:
            st.error("Failed to get job status")
            break
        
        st.session_state.job_status = status
        job_state = status.get("status", "unknown")
        
        # Progress bar
        progress = status.get("progress", 0)
        progress_placeholder.progress(progress / 100, text=f"Progress: {progress}%")
        
        # Metrics
        with metrics_placeholder.container():
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Status", job_state.upper())
            with col2:
                st.metric("Rows Generated", status.get("rows_generated", 0))
            with col3:
                st.metric("Duplicates Removed", status.get("rows_deduplicated", 0))
            with col4:
                st.metric("Chunks Complete", f"{status.get('chunks_completed', 0)}/{status.get('total_chunks', 0)}")
        
        # Check if complete
        if job_state == "completed":
            st.success("🎉 Generation completed successfully!")
            
            # Download buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                csv_data = download_results(job_id, "csv")
                if csv_data:
                    st.download_button(
                        "📥 Download CSV",
                        data=csv_data,
                        file_name=f"synthaix_{job_id}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            with col2:
                json_data = download_results(job_id, "json")
                if json_data:
                    st.download_button(
                        "📥 Download JSON",
                        data=json_data,
                        file_name=f"synthaix_{job_id}.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
            # Preview data
            if csv_data:
                st.markdown("### 👀 Data Preview")
                df = pd.read_csv(io.BytesIO(csv_data))
                st.dataframe(df.head(20), use_container_width=True)
                st.caption(f"Showing first 20 of {len(df)} rows")
            
            if st.button("🔄 Generate More Data", type="primary"):
                st.session_state.step = 1
                st.session_state.job_id = None
                st.session_state.schema = None
                st.rerun()
            
            break
        
        elif job_state == "failed":
            st.error(f"❌ Job failed: {status.get('error', 'Unknown error')}")
            if st.button("🔄 Try Again"):
                st.session_state.step = 3
                st.session_state.job_id = None
                st.rerun()
            break
        
        # Wait before next poll
        time.sleep(2)
        poll_count += 1
    
    if poll_count >= max_polls:
        st.warning("⏱️ Polling timeout. Job may still be running. Check back later.")


def main():
    """Main application."""
    render_header()
    render_sidebar()
    
    # Route to appropriate step
    if st.session_state.step == 1:
        step1_describe()
    elif st.session_state.step == 2:
        step2_edit_schema()
    elif st.session_state.step == 3:
        step3_configure()
    elif st.session_state.step == 4:
        step4_generate()
    else:
        st.error("Invalid step")


if __name__ == "__main__":
    main()
