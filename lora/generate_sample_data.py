"""
Generate a sample CSV dataset for testing the LoRA fine-tuning
Creates realistic data for various domains
"""

import pandas as pd
import random
import argparse


# Sample data templates
TECH_QUESTIONS = [
    ("What is {topic}?", "Description of {topic}..."),
    ("Explain {topic} in simple terms", "Simple explanation of {topic}..."),
    ("How does {topic} work?", "Working mechanism of {topic}..."),
    ("What are the benefits of {topic}?", "Benefits include..."),
    ("Compare {topic} with {other}", "Comparison between..."),
]

TECH_TOPICS = [
    "machine learning", "neural networks", "deep learning", "artificial intelligence",
    "data science", "Python programming", "web development", "cloud computing",
    "cybersecurity", "blockchain", "quantum computing", "edge computing",
    "natural language processing", "computer vision", "reinforcement learning",
    "DevOps", "microservices", "containerization", "APIs", "databases"
]

SCIENCE_QA = [
    ("What is photosynthesis?", "Photosynthesis is the process by which plants convert light energy into chemical energy..."),
    ("Explain Newton's laws of motion", "Newton's three laws of motion describe the relationship between forces and motion..."),
    ("What is DNA?", "DNA, or deoxyribonucleic acid, is the hereditary material in humans and almost all organisms..."),
    ("How does the human heart work?", "The heart is a muscular organ that pumps blood throughout the body..."),
    ("What causes earthquakes?", "Earthquakes are caused by the sudden release of energy in the Earth's crust..."),
]

MATH_QA = [
    ("What is calculus?", "Calculus is a branch of mathematics focused on limits, functions, derivatives, integrals..."),
    ("Explain the Pythagorean theorem", "The Pythagorean theorem states that in a right triangle, the square of the hypotenuse..."),
    ("What are prime numbers?", "Prime numbers are natural numbers greater than 1 that have no positive divisors other than 1 and themselves..."),
    ("How do you calculate probability?", "Probability is calculated as the ratio of favorable outcomes to total possible outcomes..."),
    ("What is linear algebra used for?", "Linear algebra is used in computer graphics, machine learning, physics simulations..."),
]

PROGRAMMING_QA = [
    ("What is a variable in programming?", "A variable is a named storage location that holds a value that can be changed..."),
    ("Explain object-oriented programming", "Object-oriented programming (OOP) is a programming paradigm based on objects and classes..."),
    ("What is a for loop?", "A for loop is a control flow statement that repeats a block of code a specified number of times..."),
    ("How do you handle errors in Python?", "Error handling in Python is done using try-except blocks..."),
    ("What is recursion?", "Recursion is a programming technique where a function calls itself..."),
]


def generate_tech_data(num_samples):
    """Generate technology-related Q&A pairs"""
    data = []
    for i in range(num_samples):
        template = random.choice(TECH_QUESTIONS)
        topic = random.choice(TECH_TOPICS)
        other_topic = random.choice([t for t in TECH_TOPICS if t != topic])
        
        question = template[0].format(topic=topic, other=other_topic)
        answer = f"{template[1].format(topic=topic, other=other_topic)} This is a comprehensive explanation covering multiple aspects. " \
                f"It includes practical examples and applications in real-world scenarios. " \
                f"The concept is fundamental in modern technology and has numerous implications. " \
                f"Understanding this helps in building better systems and solutions. [Sample {i}]"
        
        data.append({"question": question, "answer": answer})
    
    return data


def generate_mixed_data(num_samples):
    """Generate mixed domain Q&A pairs"""
    data = []
    all_qa = SCIENCE_QA + MATH_QA + PROGRAMMING_QA
    
    for i in range(num_samples):
        if all_qa:
            qa = random.choice(all_qa)
            question, base_answer = qa
            
            # Expand the answer
            answer = f"{base_answer} This explanation provides a foundational understanding. " \
                    f"The concept has been studied extensively and has practical applications. " \
                    f"Further research in this area continues to reveal new insights. " \
                    f"This knowledge is essential for students and professionals alike. [Sample {i}]"
            
            data.append({"question": question, "answer": answer})
        else:
            # Fallback generic data
            data.append({
                "question": f"Sample question {i}",
                "answer": f"This is a detailed answer to sample question {i}. It provides comprehensive information."
            })
    
    return data


def generate_instruction_data(num_samples):
    """Generate instruction-response format data"""
    instructions = [
        "Write a function to {task}",
        "Explain the concept of {concept}",
        "Create a tutorial about {topic}",
        "Describe how to {action}",
        "Summarize the main points of {subject}",
    ]
    
    tasks = ["sort a list", "find prime numbers", "reverse a string", "calculate factorial"]
    concepts = ["inheritance", "polymorphism", "encapsulation", "abstraction"]
    topics = ["web scraping", "data visualization", "API development", "testing"]
    actions = ["optimize code", "debug errors", "refactor functions", "write tests"]
    subjects = ["algorithms", "data structures", "design patterns", "best practices"]
    
    data = []
    for i in range(num_samples):
        template = random.choice(instructions)
        
        if "{task}" in template:
            instruction = template.format(task=random.choice(tasks))
        elif "{concept}" in template:
            instruction = template.format(concept=random.choice(concepts))
        elif "{topic}" in template:
            instruction = template.format(topic=random.choice(topics))
        elif "{action}" in template:
            instruction = template.format(action=random.choice(actions))
        else:
            instruction = template.format(subject=random.choice(subjects))
        
        response = f"Here is a comprehensive response to the instruction. " \
                  f"This includes step-by-step guidance and practical examples. " \
                  f"The approach follows industry best practices and proven methodologies. " \
                  f"Consider edge cases and error handling in your implementation. " \
                  f"Testing and validation are crucial for ensuring correctness. [Sample {i}]"
        
        data.append({"instruction": instruction, "response": response})
    
    return data


def main():
    parser = argparse.ArgumentParser(description="Generate sample dataset for LoRA fine-tuning")
    parser.add_argument("--output", type=str, default="sample_dataset.csv", help="Output CSV file path")
    parser.add_argument("--num_rows", type=int, default=5000, help="Number of rows to generate")
    parser.add_argument(
        "--format",
        type=str,
        choices=["qa", "instruction", "tech", "mixed"],
        default="qa",
        help="Data format: qa (question-answer), instruction (instruction-response), tech (tech Q&A), mixed (all domains)"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Set random seed
    random.seed(args.seed)
    
    print(f"Generating {args.num_rows} rows of {args.format} data...")
    
    # Generate data based on format
    if args.format == "tech":
        data = generate_tech_data(args.num_rows)
    elif args.format == "mixed":
        data = generate_mixed_data(args.num_rows)
    elif args.format == "instruction":
        data = generate_instruction_data(args.num_rows)
    else:  # qa
        data = generate_mixed_data(args.num_rows)
    
    # Create DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv(args.output, index=False)
    
    print(f"\n✓ Dataset created successfully!")
    print(f"  File: {args.output}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {', '.join(df.columns)}")
    print(f"\nFirst few rows:")
    print(df.head(3).to_string())
    
    print(f"\n📊 Statistics:")
    for col in df.columns:
        avg_len = df[col].str.len().mean()
        print(f"  {col}: avg length = {avg_len:.0f} chars")
    
    print(f"\n✅ Ready to use with:")
    print(f"   python train_lora.py --csv_path {args.output}")


if __name__ == "__main__":
    main()
