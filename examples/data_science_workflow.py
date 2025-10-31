#!/usr/bin/env python3
"""
Data Science workflow example using SynthAIx.
Demonstrates integration with pandas, scikit-learn, and visualization.
"""

import pandas as pd
import requests
import time
from typing import Dict, Any, List


class SynthAIxDataLoader:
    """Helper class to load synthetic data into pandas DataFrames."""
    
    def __init__(self, api_url: str = "http://localhost:8000/api/v1"):
        self.api_url = api_url
    
    def generate_dataframe(
        self,
        prompt: str,
        n_rows: int,
        wait: bool = True
    ) -> pd.DataFrame:
        """
        Generate synthetic data and load into DataFrame.
        
        Args:
            prompt: Natural language description
            n_rows: Number of rows to generate
            wait: Whether to wait for completion
            
        Returns:
            pandas DataFrame with generated data
        """
        # Translate schema
        response = requests.post(
            f"{self.api_url}/schema/translate",
            json={"prompt": prompt}
        )
        schema = response.json()["schema"]
        
        # Start generation
        response = requests.post(
            f"{self.api_url}/data/generate",
            json={
                "schema": schema,
                "total_rows": n_rows,
                "enable_deduplication": True
            }
        )
        job_id = response.json()["job_id"]
        
        if not wait:
            return job_id  # Return job ID for later retrieval
        
        # Poll until complete
        while True:
            response = requests.get(f"{self.api_url}/jobs/{job_id}/status")
            status = response.json()
            
            if status["status"] == "completed":
                df = pd.DataFrame(status["data"])
                return df
            elif status["status"] == "failed":
                raise RuntimeError(f"Generation failed: {status.get('error')}")
            
            time.sleep(2)


# Example 1: E-commerce Analytics
def example_ecommerce_analytics():
    """Generate and analyze e-commerce transaction data."""
    
    print("=" * 60)
    print("Example 1: E-commerce Analytics")
    print("=" * 60)
    
    loader = SynthAIxDataLoader()
    
    # Generate transaction data
    prompt = """
    Generate e-commerce transactions with:
    - order_id (UUID)
    - customer_id (UUID)
    - product_name (string)
    - category (string: Electronics, Clothing, Home, Books)
    - price (float: 10-500)
    - quantity (integer: 1-5)
    - order_date (date)
    - status (string: completed, pending, cancelled)
    """
    
    print("\nGenerating 500 e-commerce transactions...")
    df = loader.generate_dataframe(prompt, n_rows=500)
    
    print(f"\n✅ Generated {len(df)} transactions")
    print(f"\nDataFrame Info:")
    print(df.info())
    
    print(f"\nFirst 5 rows:")
    print(df.head())
    
    # Analytics
    print("\n--- Analytics ---")
    
    # Total revenue
    if 'price' in df.columns and 'quantity' in df.columns:
        df['revenue'] = df['price'] * df['quantity']
        print(f"\nTotal Revenue: ${df['revenue'].sum():,.2f}")
        print(f"Average Order Value: ${df['revenue'].mean():.2f}")
    
    # Sales by category
    if 'category' in df.columns and 'revenue' in df.columns:
        print("\nRevenue by Category:")
        print(df.groupby('category')['revenue'].sum().sort_values(ascending=False))
    
    # Order status distribution
    if 'status' in df.columns:
        print("\nOrder Status Distribution:")
        print(df['status'].value_counts())
    
    return df


# Example 2: Customer Churn Prediction Data
def example_customer_churn():
    """Generate customer data for churn prediction modeling."""
    
    print("\n" + "=" * 60)
    print("Example 2: Customer Churn Prediction Dataset")
    print("=" * 60)
    
    loader = SynthAIxDataLoader()
    
    prompt = """
    Generate customer data for churn prediction with:
    - customer_id (UUID)
    - tenure_months (integer: 1-60)
    - monthly_charges (float: 20-150)
    - total_charges (float)
    - contract_type (string: month-to-month, one-year, two-year)
    - payment_method (string: credit-card, bank-transfer, electronic-check)
    - internet_service (string: fiber, dsl, no)
    - tech_support (boolean)
    - churn (boolean)
    """
    
    print("\nGenerating customer churn dataset...")
    df = loader.generate_dataframe(prompt, n_rows=1000)
    
    print(f"\n✅ Generated {len(df)} customer records")
    
    # Data quality checks
    print("\n--- Data Quality ---")
    print(f"Missing values:\n{df.isnull().sum()}")
    print(f"\nDuplicates: {df.duplicated().sum()}")
    
    # Feature engineering example
    if 'tenure_months' in df.columns and 'total_charges' in df.columns:
        df['avg_monthly_charges'] = df['total_charges'] / df['tenure_months']
        print("\n✅ Added feature: avg_monthly_charges")
    
    # Target distribution
    if 'churn' in df.columns:
        print("\nChurn Distribution:")
        print(df['churn'].value_counts(normalize=True))
    
    # Export for ML pipeline
    output_file = "/tmp/customer_churn_data.csv"
    df.to_csv(output_file, index=False)
    print(f"\n💾 Saved to: {output_file}")
    
    return df


# Example 3: Time Series Data
def example_iot_timeseries():
    """Generate IoT sensor time series data."""
    
    print("\n" + "=" * 60)
    print("Example 3: IoT Sensor Time Series")
    print("=" * 60)
    
    loader = SynthAIxDataLoader()
    
    prompt = """
    Generate IoT sensor readings with:
    - sensor_id (UUID)
    - timestamp (datetime)
    - temperature (float: 15-35)
    - humidity (float: 30-90)
    - pressure (float: 980-1050)
    - battery_level (float: 0-100)
    - location (string)
    """
    
    print("\nGenerating sensor data...")
    df = loader.generate_dataframe(prompt, n_rows=2000)
    
    print(f"\n✅ Generated {len(df)} sensor readings")
    
    # Convert timestamp if present
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
    
    # Time series analysis
    print("\n--- Time Series Analysis ---")
    
    if 'temperature' in df.columns:
        print(f"\nTemperature Stats:")
        print(df['temperature'].describe())
    
    # Resample by hour (if timestamp is available)
    if 'timestamp' in df.columns and 'temperature' in df.columns:
        df.set_index('timestamp', inplace=True)
        hourly = df['temperature'].resample('H').mean()
        print(f"\nHourly temperature readings: {len(hourly)}")
    
    return df


# Example 4: A/B Test Data
def example_ab_test():
    """Generate A/B test experiment data."""
    
    print("\n" + "=" * 60)
    print("Example 4: A/B Test Experiment Data")
    print("=" * 60)
    
    loader = SynthAIxDataLoader()
    
    prompt = """
    Generate A/B test data with:
    - user_id (UUID)
    - variant (string: A, B)
    - conversion (boolean)
    - session_duration_seconds (integer: 10-600)
    - page_views (integer: 1-20)
    - signup_date (date)
    - device_type (string: mobile, desktop, tablet)
    """
    
    print("\nGenerating A/B test data...")
    df = loader.generate_dataframe(prompt, n_rows=10000)
    
    print(f"\n✅ Generated {len(df)} experiment records")
    
    # A/B test analysis
    print("\n--- A/B Test Results ---")
    
    if 'variant' in df.columns and 'conversion' in df.columns:
        results = df.groupby('variant')['conversion'].agg(['count', 'sum', 'mean'])
        results.columns = ['Total Users', 'Conversions', 'Conversion Rate']
        print("\n", results)
        
        # Statistical significance (simplified)
        conv_a = df[df['variant'] == 'A']['conversion'].mean()
        conv_b = df[df['variant'] == 'B']['conversion'].mean()
        lift = ((conv_b - conv_a) / conv_a) * 100
        
        print(f"\n📊 Conversion Lift (B vs A): {lift:+.2f}%")
    
    # Device breakdown
    if 'device_type' in df.columns and 'conversion' in df.columns:
        print("\nConversion by Device:")
        print(df.groupby('device_type')['conversion'].mean().sort_values(ascending=False))
    
    return df


# Main execution
def main():
    """Run all examples."""
    
    print("\n🤖 SynthAIx Data Science Integration Examples")
    print("=" * 60)
    
    try:
        # Run examples
        df1 = example_ecommerce_analytics()
        df2 = example_customer_churn()
        df3 = example_iot_timeseries()
        df4 = example_ab_test()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
        print("\n💡 Next Steps:")
        print("  - Use the generated DataFrames in your ML pipelines")
        print("  - Visualize with matplotlib, seaborn, or plotly")
        print("  - Train models with scikit-learn, XGBoost, etc.")
        print("  - Export to various formats (CSV, Parquet, SQL)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure SynthAIx is running:")
        print("  docker-compose up -d")


if __name__ == "__main__":
    main()
