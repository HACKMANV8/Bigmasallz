"""
Merge LoRA adapter with base model for deployment
This creates a single model that doesn't need the adapter
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import argparse


def merge_lora_model(base_model_name, lora_model_path, output_path):
    """
    Merge LoRA adapter weights with the base model
    and save as a standalone model
    """
    print(f"Loading base model: {base_model_name}")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    
    print(f"Loading LoRA adapter from: {lora_model_path}")
    model = PeftModel.from_pretrained(base_model, lora_model_path)
    
    print("Merging LoRA weights with base model...")
    model = model.merge_and_unload()
    
    print(f"Saving merged model to: {output_path}")
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)
    
    print("\n✓ Model merged successfully!")
    print(f"You can now use the model from: {output_path}")
    print("\nTo use the merged model:")
    print(f"  from transformers import AutoModelForCausalLM, AutoTokenizer")
    print(f"  model = AutoModelForCausalLM.from_pretrained('{output_path}')")
    print(f"  tokenizer = AutoTokenizer.from_pretrained('{output_path}')")


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapter with base model")
    parser.add_argument(
        "--base_model",
        type=str,
        required=True,
        help="Base model name (same as used in training)",
    )
    parser.add_argument(
        "--lora_model",
        type=str,
        required=True,
        help="Path to LoRA adapter",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output path for merged model",
    )
    
    args = parser.parse_args()
    
    merge_lora_model(args.base_model, args.lora_model, args.output)


if __name__ == "__main__":
    main()
