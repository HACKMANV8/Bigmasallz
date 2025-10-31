"""Streamlit frontend for Synthetic Data Generator."""

import json
import time

import pandas as pd
import requests
import streamlit as st

# Configure page
st.set_page_config(
    page_title="Synthetic Data Generator",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8080"


def check_api_health():
    """Check if API server is healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def extract_schema(user_input, context=None, example_data=None):
    """Extract schema from natural language."""
    try:
        payload = {
            "user_input": user_input,
            "context": context or {},
            "example_data": example_data
        }
        response = requests.post(
            f"{API_BASE_URL}/schema/extract",
            json=payload,
            timeout=480  # 2 minutes for schema extraction
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to extract schema: {e}")
        return None


def create_job(schema, total_rows, chunk_size=1000, output_format="csv"):
    """Create a data generation job."""
    try:
        payload = {
            "schema": schema,
            "total_rows": total_rows,
            "chunk_size": chunk_size,
            "output_format": output_format,
            "storage_type": "disk",
            "uniqueness_fields": []
        }
        response = requests.post(
            f"{API_BASE_URL}/jobs/create",
            json=payload,
            timeout=None  # No timeout - job creation is async
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to create job: {e}")
        return None


def get_job_status(job_id):
    """Get job status."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/jobs/{job_id}/status",
            timeout=30  # Longer timeout for status checks
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to get job status: {e}")
        return None


def get_job_details(job_id):
    """Get detailed job information."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/jobs/{job_id}",
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to get job details: {e}")
        return None


def list_jobs(status=None):
    """List all jobs."""
    try:
        params = {"status": status} if status else {}
        response = requests.get(
            f"{API_BASE_URL}/jobs/",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to list jobs: {e}")
        return None


def control_job(job_id, action):
    """Control job (pause, resume, cancel)."""
    try:
        payload = {
            "job_id": str(job_id),
            "action": action
        }
        response = requests.post(
            f"{API_BASE_URL}/jobs/{job_id}/control",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to {action} job: {e}")
        return None


def preview_job_output(job_id, rows=10):
    """Preview job output."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/jobs/{job_id}/preview",
            params={"rows": rows},
            timeout=60  # Longer timeout for preview
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to preview output: {e}")
        return None


def download_job_output(job_id):
    """Download job output."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/jobs/{job_id}/download",
            timeout=300  # 5 minutes for large file downloads
        )
        response.raise_for_status()
        return response.content
    except Exception as e:
        st.error(f"Failed to download output: {e}")
        return None


# Main UI
def main():
    """Main application."""

    # Header
    st.title("🎲 Synthetic Data Generator")
    st.markdown("Generate realistic synthetic datasets using AI")

    # Check API health
    if not check_api_health():
        st.error("⚠️ API server is not running. Please start the API server at http://localhost:8080")
        st.code("uvicorn src.api_server.app:app --reload", language="bash")
        return

    st.success("✅ Connected to API server")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Create Dataset", "Monitor Jobs", "Browse Jobs"]
    )

    if page == "Create Dataset":
        create_dataset_page()
    elif page == "Monitor Jobs":
        monitor_jobs_page()
    elif page == "Browse Jobs":
        browse_jobs_page()


def create_dataset_page():
    """Page for creating new datasets."""
    st.header("Create New Dataset")

    # Input method selection
    input_method = st.radio(
        "How would you like to define your schema?",
        ["Natural Language", "JSON Schema"]
    )

    if input_method == "Natural Language":
        st.subheader("Describe Your Dataset")

        user_input = st.text_area(
            "Dataset Description",
            placeholder="Example: Generate customer data with name, email, age, and purchase history",
            height=150
        )

        col1, col2 = st.columns(2)

        with col1:
            with st.expander("Additional Context (Optional)"):
                context_text = st.text_area(
                    "Provide additional context",
                    placeholder='{"domain": "e-commerce", "region": "US"}',
                    height=100
                )

        with col2:
            with st.expander("Example Data (Optional)"):
                example_data = st.text_area(
                    "Provide example data",
                    placeholder="name,email,age\nJohn Doe,john@example.com,30",
                    height=100
                )

        if st.button("Extract Schema", type="primary"):
            if not user_input:
                st.warning("Please provide a dataset description")
                return

            with st.spinner("Extracting schema from your description..."):
                context = None
                if context_text:
                    try:
                        context = json.loads(context_text)
                    except:
                        st.warning("Invalid JSON in context, ignoring")

                result = extract_schema(user_input, context, example_data)

                if result:
                    st.session_state.schema = result["schema"]
                    st.success("✅ Schema extracted successfully!")
                    st.json(result["schema"])

                    if result.get("metadata", {}).get("suggestions"):
                        with st.expander("💡 Suggestions"):
                            for suggestion in result["metadata"]["suggestions"]:
                                st.info(suggestion)

    else:  # JSON Schema
        st.subheader("Provide JSON Schema")

        schema_text = st.text_area(
            "JSON Schema",
            placeholder=json.dumps({
                "fields": [
                    {
                        "name": "id",
                        "type": "uuid",
                        "description": "Unique identifier"
                    },
                    {
                        "name": "name",
                        "type": "string",
                        "description": "Customer name"
                    }
                ]
            }, indent=2),
            height=300
        )

        if st.button("Load Schema", type="primary"):
            if not schema_text:
                st.warning("Please provide a schema")
                return

            try:
                schema = json.loads(schema_text)
                st.session_state.schema = schema
                st.success("✅ Schema loaded successfully!")
                st.json(schema)
            except Exception as e:
                st.error(f"Invalid JSON: {e}")

    # Generation parameters
    if "schema" in st.session_state:
        st.divider()
        st.subheader("Generation Parameters")

        col1, col2, col3 = st.columns(3)

        with col1:
            total_rows = st.number_input(
                "Total Rows",
                min_value=1,
                max_value=100000,
                value=1000,
                step=100
            )

        with col2:
            chunk_size = st.number_input(
                "Chunk Size",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100
            )

        with col3:
            output_format = st.selectbox(
                "Output Format",
                ["csv", "json", "parquet"]
            )

        if st.button("🚀 Generate Dataset", type="primary", use_container_width=True):
            with st.spinner("Creating generation job..."):
                result = create_job(
                    schema=st.session_state.schema,
                    total_rows=total_rows,
                    chunk_size=chunk_size,
                    output_format=output_format
                )

                if result:
                    st.success(f"✅ Job created: {result['job_id']}")
                    st.session_state.current_job_id = result["job_id"]
                    st.info(result["message"])
                    time.sleep(2)
                    st.rerun()


def monitor_jobs_page():
    """Page for monitoring job progress."""
    st.header("Monitor Jobs")

    # Job ID input
    job_id_input = st.text_input(
        "Job ID",
        value=st.session_state.get("current_job_id", ""),
        placeholder="Enter job ID to monitor"
    )

    if not job_id_input:
        st.info("Enter a job ID to start monitoring")
        return

    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (every 2 seconds)", value=True)

    # Create placeholder for live updates
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    details_placeholder = st.empty()
    preview_placeholder = st.empty()

    while True:
        with status_placeholder.container():
            status = get_job_status(job_id_input)

            if status:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Status", status["status"])

                with col2:
                    st.metric("Progress", f"{status['progress_percentage']:.1f}%")

                with col3:
                    st.metric("Rows Generated", f"{status['rows_generated']:,}")

                with col4:
                    st.metric("Chunks", f"{status['chunks_completed']}/{status['total_chunks']}")

                # Progress bar
                with progress_placeholder:
                    st.progress(status["progress_percentage"] / 100)

                # Control buttons
                if status["status"] == "generating":
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("⏸️ Pause Job"):
                            control_job(job_id_input, "pause")
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel Job"):
                            control_job(job_id_input, "cancel")
                            st.rerun()

                elif status["status"] == "paused":
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("▶️ Resume Job"):
                            control_job(job_id_input, "resume")
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel Job"):
                            control_job(job_id_input, "cancel")
                            st.rerun()

                elif status["status"] == "completed":
                    st.success("✅ Job completed successfully!")

                    # Preview data
                    with preview_placeholder:
                        st.subheader("Data Preview")
                        preview = preview_job_output(job_id_input, rows=20)
                        if preview and preview["data"]:
                            df = pd.DataFrame(preview["data"])
                            st.dataframe(df, use_container_width=True)
                            st.caption(f"Showing {len(preview['data'])} of {preview['total_rows']} rows")

                    # Download button
                    if st.button("📥 Download Dataset", type="primary"):
                        with st.spinner("Downloading..."):
                            data = download_job_output(job_id_input)
                            if data:
                                st.download_button(
                                    label="💾 Save File",
                                    data=data,
                                    file_name=f"synthetic_data_{job_id_input}.csv",
                                    mime="text/csv"
                                )

                elif status["status"] == "failed":
                    st.error(f"❌ Job failed: {status.get('error_message', 'Unknown error')}")

                # Job details
                with details_placeholder:
                    with st.expander("Job Details"):
                        details = get_job_details(job_id_input)
                        if details:
                            st.json(details)

        if not auto_refresh or status.get("status") in ["completed", "failed", "cancelled"]:
            break

        time.sleep(2)
        st.rerun()


def browse_jobs_page():
    """Page for browsing all jobs."""
    st.header("Browse Jobs")

    # Filter options
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "generating", "paused", "completed", "failed", "cancelled"]
        )

    with col2:
        limit = st.number_input("Max Results", min_value=10, max_value=500, value=50, step=10)

    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()

    # Get jobs
    status_param = None if status_filter == "All" else status_filter
    result = list_jobs(status=status_param)

    if result and result["jobs"]:
        st.success(f"Found {result['total']} jobs")

        # Display jobs as cards
        for job in result["jobs"]:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                with col1:
                    st.markdown(f"**Job ID:** `{job['specification']['job_id']}`")
                    st.caption(f"Created: {job['specification']['created_at']}")

                with col2:
                    status_emoji = {
                        "completed": "✅",
                        "generating": "⏳",
                        "pending": "⏱️",
                        "failed": "❌",
                        "paused": "⏸️",
                        "cancelled": "🚫"
                    }
                    st.markdown(f"{status_emoji.get(job['progress']['status'], '⚪')} **{job['progress']['status']}**")

                with col3:
                    st.metric("Progress", f"{job['progress']['progress_percentage']:.1f}%")

                with col4:
                    if st.button("View", key=f"view_{job['specification']['job_id']}"):
                        st.session_state.current_job_id = job['specification']['job_id']
                        st.switch_page("pages/monitor_jobs.py") if hasattr(st, "switch_page") else st.rerun()

                st.divider()
    else:
        st.info("No jobs found")


if __name__ == "__main__":
    # Initialize session state
    if "schema" not in st.session_state:
        st.session_state.schema = None
    if "current_job_id" not in st.session_state:
        st.session_state.current_job_id = None

    main()
