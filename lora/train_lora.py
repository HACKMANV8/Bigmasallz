"""
Fine-tune a small language model with LoRA
For hackathon project - efficient training on consumer hardware
"""

import os
import torch
import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType,
)
import argparse


def load_and_prepare_data(csv_path, tokenizer, max_length=512):
    """Load CSV data and prepare for training"""
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Drop rows with missing values in critical columns
    initial_rows = len(df)
    df = df.dropna(subset=[col for col in df.columns if df[col].dtype == 'object' or col in df.columns[:5]])
    if len(df) < initial_rows:
        print(f"Dropped {initial_rows - len(df)} rows with missing values")
    
    # Check if the CSV has 'text' column or needs formatting
    # Adjust this based on your CSV structure
    if 'text' not in df.columns:
        # If you have instruction-response format
        if 'instruction' in df.columns and 'response' in df.columns:
            df['text'] = df.apply(
                lambda row: f"### Instruction:\n{row['instruction']}\n\n### Response:\n{row['response']}", 
                axis=1
            )
        # If you have prompt-completion format
        elif 'prompt' in df.columns and 'completion' in df.columns:
            df['text'] = df.apply(
                lambda row: f"{row['prompt']}\n{row['completion']}", 
                axis=1
            )
        # If you have question-answer format
        elif 'question' in df.columns and 'answer' in df.columns:
            df['text'] = df.apply(
                lambda row: f"Question: {row['question']}\nAnswer: {row['answer']}", 
                axis=1
            )
        # Auto-format: Try to create meaningful text from available columns
        else:
            print("No standard format detected. Auto-generating text format...")
            
            # Try to find name/title and description columns
            name_col = None
            desc_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'name' in col_lower or 'title' in col_lower:
                    name_col = col
                if 'description' in col_lower or 'desc' in col_lower or 'summary' in col_lower:
                    desc_col = col
            
            if name_col and desc_col:
                # Create Q&A format from name and description
                df['text'] = df.apply(
                    lambda row: f"Question: What is {row[name_col]}?\nAnswer: {row[desc_col]}", 
                    axis=1
                )
                print(f"Created Q&A format using columns: {name_col} and {desc_col}")
            elif desc_col:
                # Use description only
                df['text'] = df[desc_col].astype(str)
                print(f"Using column '{desc_col}' as training text")
            else:
                # Fallback: concatenate all text columns
                text_cols = [col for col in df.columns if df[col].dtype == 'object']
                if text_cols:
                    df['text'] = df[text_cols].apply(
                        lambda row: ' | '.join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)]), 
                        axis=1
                    )
                    print(f"Concatenated {len(text_cols)} text columns: {text_cols}")
                else:
                    raise ValueError(
                        "Could not create training text. CSV must have either:\n"
                        "  - 'text' column\n"
                        "  - 'instruction' + 'response' columns\n"
                        "  - 'prompt' + 'completion' columns\n"
                        "  - 'question' + 'answer' columns\n"
                        "  - 'name'/'title' + 'description' columns\n"
                        "  - Or at least one text column"
                    )
    
    # Show sample of generated text
    print("\n" + "="*60)
    print("Sample training text (first 3 examples):")
    print("="*60)
    for i, text in enumerate(df['text'].head(3)):
        print(f"\nExample {i+1}:")
        print(text[:300] + "..." if len(text) > 300 else text)
    print("="*60 + "\n")
    
    # Convert to Hugging Face dataset
    dataset = Dataset.from_pandas(df[['text']])
    
    # Tokenize the dataset
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
            padding="max_length",
        )
    
    print("Tokenizing dataset...")
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names,
        desc="Tokenizing",
    )
    
    return tokenized_dataset


def create_model_and_tokenizer(model_name, use_8bit=False):
    """Load model and tokenizer with optional 8-bit quantization"""
    print(f"Loading model: {model_name}")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    # Add pad token if it doesn't exist
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    # Load model with optional quantization
    if use_8bit:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            load_in_8bit=True,
            device_map="auto",
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(model)
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            trust_remote_code=True,
        )
    
    return model, tokenizer


def setup_lora(model, lora_r=8, lora_alpha=16, lora_dropout=0.05):
    """Configure LoRA for the model"""
    print("Setting up LoRA configuration...")
    
    # Auto-detect target modules based on model architecture
    model_type = model.config.model_type.lower()
    print(f"Detected model type: {model_type}")
    
    # Define target modules for different architectures
    if model_type in ["gpt2", "gpt_neo", "gpt_neox", "gptj"]:
        target_modules = ["c_attn", "c_proj"]  # GPT-2 style
    elif model_type in ["llama", "mistral", "mixtral"]:
        target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
    elif model_type in ["phi", "phi-msft"]:
        target_modules = ["q_proj", "v_proj", "dense"]
    elif model_type == "opt":
        target_modules = ["q_proj", "v_proj"]
    elif model_type in ["bloom", "bloomz"]:
        target_modules = ["query_key_value"]
    else:
        # Fallback: try to find attention modules automatically
        print(f"Warning: Unknown model type '{model_type}', attempting auto-detection...")
        target_modules = []
        for name, module in model.named_modules():
            if any(key in name.lower() for key in ["attn", "attention"]):
                # Get the last part of the module name
                module_name = name.split(".")[-1]
                if module_name not in target_modules and hasattr(module, "weight"):
                    target_modules.append(module_name)
        
        if not target_modules:
            # Ultimate fallback
            target_modules = ["c_attn"]
            print(f"Warning: Could not auto-detect modules, using default: {target_modules}")
    
    print(f"Using target modules: {target_modules}")
    
    # LoRA configuration
    lora_config = LoraConfig(
        r=lora_r,  # Rank of the low-rank matrices
        lora_alpha=lora_alpha,  # Scaling factor
        target_modules=target_modules,
        lora_dropout=lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    
    # Apply LoRA to model
    model = get_peft_model(model, lora_config)
    
    # Print trainable parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Trainable params: {trainable_params:,} || Total params: {total_params:,} || "
          f"Trainable %: {100 * trainable_params / total_params:.2f}%")
    
    return model


def train_model(
    model,
    tokenizer,
    train_dataset,
    output_dir="./lora_model",
    num_epochs=3,
    batch_size=4,
    learning_rate=2e-4,
    gradient_accumulation_steps=4,
    warmup_steps=100,
    logging_steps=10,
    save_steps=500,
    use_wandb=False,
):
    """Train the model with LoRA"""
    print("Starting training...")
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        fp16=torch.cuda.is_available(),  # Use mixed precision if GPU available
        logging_steps=logging_steps,
        save_steps=save_steps,
        save_total_limit=3,
        warmup_steps=warmup_steps,
        report_to="wandb" if use_wandb else "none",
        optim="adamw_torch",
        lr_scheduler_type="cosine",
        gradient_checkpointing=True,
        dataloader_num_workers=4,
        group_by_length=True,  # Group sequences of similar length for efficiency
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # We're doing causal language modeling, not masked LM
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
    )
    
    # Train
    trainer.train()
    
    # Save final model
    print(f"Saving final model to {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    return trainer


def main():
    parser = argparse.ArgumentParser(description="Fine-tune a language model with LoRA")
    
    # Model and data arguments
    parser.add_argument(
        "--model_name",
        type=str,
        default="gpt2",  # Small ~100M parameter model
        help="Model name or path (default: gpt2, alternatives: microsoft/phi-1_5, EleutherAI/pythia-160m)",
    )
    parser.add_argument(
        "--csv_path",
        type=str,
        required=True,
        help="Path to CSV file with training data",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./lora_finetuned_model",
        help="Output directory for the fine-tuned model",
    )
    
    # Training arguments
    parser.add_argument("--num_epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Training batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--max_length", type=int, default=512, help="Maximum sequence length")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4, help="Gradient accumulation steps")
    
    # LoRA arguments
    parser.add_argument("--lora_r", type=int, default=8, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=16, help="LoRA alpha")
    parser.add_argument("--lora_dropout", type=float, default=0.05, help="LoRA dropout")
    
    # Other arguments
    parser.add_argument("--use_8bit", action="store_true", help="Use 8-bit quantization")
    parser.add_argument("--use_wandb", action="store_true", help="Log to Weights & Biases")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Set seed for reproducibility
    torch.manual_seed(args.seed)
    
    # Initialize wandb if requested
    if args.use_wandb:
        import wandb
        wandb.init(project="lora-finetuning", config=vars(args))
    
    # Load model and tokenizer
    model, tokenizer = create_model_and_tokenizer(args.model_name, args.use_8bit)
    
    # Setup LoRA
    model = setup_lora(model, args.lora_r, args.lora_alpha, args.lora_dropout)
    
    # Load and prepare data
    train_dataset = load_and_prepare_data(args.csv_path, tokenizer, args.max_length)
    
    # Train model
    trainer = train_model(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        output_dir=args.output_dir,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        use_wandb=args.use_wandb,
    )
    
    print("\n" + "="*50)
    print("Training completed successfully!")
    print(f"Model saved to: {args.output_dir}")
    print("="*50)


if __name__ == "__main__":
    main()
