"""
Inference script for the LoRA fine-tuned model
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import argparse


def load_model(base_model_name, lora_model_path):
    """Load the base model with LoRA weights"""
    print(f"Loading base model: {base_model_name}")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        device_map="auto",
        trust_remote_code=True,
    )
    
    print(f"Loading LoRA weights from: {lora_model_path}")
    model = PeftModel.from_pretrained(base_model, lora_model_path)
    model.eval()
    
    return model, tokenizer


def generate_response(model, tokenizer, prompt, max_length=200, temperature=0.7, top_p=0.9):
    """Generate a response from the model"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            num_return_sequences=1,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


def main():
    parser = argparse.ArgumentParser(description="Run inference with LoRA fine-tuned model")
    parser.add_argument(
        "--base_model",
        type=str,
        default="gpt2",
        help="Base model name (same as used in training)",
    )
    parser.add_argument(
        "--lora_model",
        type=str,
        default="./lora_finetuned_model",
        help="Path to LoRA fine-tuned model",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Input prompt for generation",
    )
    parser.add_argument(
        "--max_length",
        type=int,
        default=200,
        help="Maximum length of generated text",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    
    args = parser.parse_args()
    
    # Load model
    model, tokenizer = load_model(args.base_model, args.lora_model)
    
    if args.interactive:
        print("\n" + "="*50)
        print("Interactive mode - Type 'quit' or 'exit' to stop")
        print("="*50 + "\n")
        
        while True:
            prompt = input("\nPrompt: ").strip()
            if prompt.lower() in ['quit', 'exit', 'q']:
                break
            
            if not prompt:
                continue
            
            print("\nGenerating response...\n")
            response = generate_response(
                model, 
                tokenizer, 
                prompt, 
                max_length=args.max_length,
                temperature=args.temperature
            )
            print(f"Response:\n{response}\n")
            print("-"*50)
    else:
        if not args.prompt:
            print("Error: Please provide --prompt or use --interactive mode")
            return
        
        print(f"\nPrompt: {args.prompt}\n")
        print("Generating response...\n")
        response = generate_response(
            model, 
            tokenizer, 
            args.prompt,
            max_length=args.max_length,
            temperature=args.temperature
        )
        print(f"Response:\n{response}\n")


if __name__ == "__main__":
    main()
