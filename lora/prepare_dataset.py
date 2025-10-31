"""
Script to help prepare and validate your dataset
"""

import pandas as pd
import argparse


def analyze_csv(csv_path):
    """Analyze the CSV file and provide statistics"""
    print(f"\nAnalyzing: {csv_path}")
    print("="*60)
    
    df = pd.read_csv(csv_path)
    
    print(f"\nDataset Statistics:")
    print(f"  Total rows: {len(df):,}")
    print(f"  Total columns: {len(df.columns)}")
    print(f"\nColumns:")
    for col in df.columns:
        print(f"  - {col} (type: {df[col].dtype})")
    
    print(f"\nMissing values:")
    missing = df.isnull().sum()
    for col, count in missing.items():
        if count > 0:
            print(f"  - {col}: {count} ({count/len(df)*100:.2f}%)")
    
    print(f"\nFirst 3 rows:")
    print(df.head(3).to_string())
    
    print(f"\nText length statistics (in characters):")
    for col in df.columns:
        if df[col].dtype == 'object':  # String columns
            lengths = df[col].astype(str).str.len()
            print(f"  {col}:")
            print(f"    Min: {lengths.min()}")
            print(f"    Max: {lengths.max()}")
            print(f"    Mean: {lengths.mean():.1f}")
            print(f"    Median: {lengths.median():.1f}")


def create_sample_dataset(output_path, num_rows=5000):
    """Create a sample dataset for testing"""
    import random
    
    print(f"Creating sample dataset with {num_rows} rows...")
    
    # Sample questions and answers (you can customize this)
    topics = ["technology", "science", "history", "mathematics", "programming"]
    
    data = []
    for i in range(num_rows):
        topic = random.choice(topics)
        data.append({
            'instruction': f'Explain {topic} concept number {i}',
            'response': f'This is a detailed explanation about {topic}. '
                       f'It covers various aspects and provides comprehensive information. '
                       f'Sample response {i} for demonstration purposes.'
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Sample dataset saved to: {output_path}")
    print(f"Shape: {df.shape}")


def validate_dataset(csv_path):
    """Validate that the dataset is suitable for training"""
    print(f"\nValidating dataset: {csv_path}")
    print("="*60)
    
    df = pd.read_csv(csv_path)
    issues = []
    
    # Check for required columns
    valid_formats = [
        {'text'},
        {'instruction', 'response'},
        {'prompt', 'completion'},
        {'question', 'answer'}
    ]
    
    columns_set = set(df.columns)
    format_match = any(fmt.issubset(columns_set) for fmt in valid_formats)
    
    if not format_match:
        issues.append(
            "❌ Dataset must have one of these column formats:\n"
            "   - 'text'\n"
            "   - 'instruction' + 'response'\n"
            "   - 'prompt' + 'completion'\n"
            "   - 'question' + 'answer'"
        )
    else:
        print("✓ Column format is valid")
    
    # Check for empty values
    if df.isnull().any().any():
        issues.append(f"⚠️  Dataset contains {df.isnull().sum().sum()} missing values")
    else:
        print("✓ No missing values")
    
    # Check dataset size
    if len(df) < 100:
        issues.append(f"⚠️  Dataset is small ({len(df)} rows). Consider having at least 1000 rows for better results")
    else:
        print(f"✓ Dataset size is adequate ({len(df):,} rows)")
    
    # Check text lengths
    for col in df.columns:
        if df[col].dtype == 'object':
            avg_length = df[col].astype(str).str.len().mean()
            if avg_length < 10:
                issues.append(f"⚠️  Column '{col}' has very short text (avg: {avg_length:.1f} chars)")
    
    print("\n" + "="*60)
    if issues:
        print("Issues found:")
        for issue in issues:
            print(issue)
    else:
        print("✓ Dataset validation passed!")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Dataset preparation and validation")
    parser.add_argument("--csv_path", type=str, help="Path to CSV file to analyze/validate")
    parser.add_argument("--analyze", action="store_true", help="Analyze the CSV file")
    parser.add_argument("--validate", action="store_true", help="Validate the CSV file for training")
    parser.add_argument(
        "--create_sample",
        action="store_true",
        help="Create a sample dataset"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="sample_dataset.csv",
        help="Output path for sample dataset"
    )
    parser.add_argument(
        "--num_rows",
        type=int,
        default=5000,
        help="Number of rows for sample dataset"
    )
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_dataset(args.output, args.num_rows)
    
    if args.csv_path:
        if args.analyze:
            analyze_csv(args.csv_path)
        if args.validate:
            validate_dataset(args.csv_path)
        if not args.analyze and not args.validate:
            # Do both by default
            analyze_csv(args.csv_path)
            validate_dataset(args.csv_path)
    elif not args.create_sample:
        parser.print_help()


if __name__ == "__main__":
    main()
