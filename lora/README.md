# LoRA Fine-tuning for Language Models 🚀

Fine-tune a small ~100M parameter language model with LoRA (Low-Rank Adaptation) for efficient training on your dataset.

## 🎯 Features

- **Efficient Training**: Uses LoRA to reduce trainable parameters by >95%
- **Memory Efficient**: Optional 8-bit quantization for limited GPU memory
- **Flexible Data Format**: Supports multiple CSV formats
- **Easy Inference**: Simple script to test your fine-tuned model
- **Hackathon Ready**: Fast setup and training

## 📋 Requirements

- Python 3.8+
- CUDA-capable GPU (recommended) or CPU
- 8GB+ RAM (16GB+ recommended)

## 🔧 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Your Dataset

Your CSV file should have one of these formats:

**Option A: Text column**
```csv
text
"Your complete training text here..."
"Another training example..."
```

**Option B: Instruction-Response**
```csv
instruction,response
"Explain photosynthesis","Photosynthesis is the process..."
"What is Python?","Python is a programming language..."
```

**Option C: Question-Answer**
```csv
question,answer
"What is AI?","Artificial Intelligence is..."
"Define machine learning","Machine learning is..."
```

**Option D: Prompt-Completion**
```csv
prompt,completion
"Write a poem about","Roses are red, violets are blue..."
"Explain quantum","Quantum physics deals with..."
```

### 3. Validate Your Dataset

```bash
python prepare_dataset.py --csv_path your_data.csv --validate
```

To create a sample dataset for testing:
```bash
python prepare_dataset.py --create_sample --output sample_data.csv --num_rows 5000
```

## 🚀 Training

### Basic Training

```bash
python train_lora.py --csv_path your_data.csv --output_dir ./my_finetuned_model
```

### Advanced Training Options

```bash
python train_lora.py \
    --csv_path your_data.csv \
    --model_name gpt2 \
    --output_dir ./my_model \
    --num_epochs 3 \
    --batch_size 4 \
    --learning_rate 2e-4 \
    --lora_r 8 \
    --lora_alpha 16 \
    --max_length 512
```

### For Limited GPU Memory (8-bit quantization)

```bash
python train_lora.py \
    --csv_path your_data.csv \
    --output_dir ./my_model \
    --use_8bit \
    --batch_size 2
```

### Available Base Models

- `gpt2` (~124M params) - Default, good for general text
- `microsoft/phi-1_5` (~1.3B params) - Better quality, needs more memory
- `EleutherAI/pythia-160m` (~160M params) - Alternative small model
- `facebook/opt-125m` (~125M params) - Another option

## 🎮 Inference

### Interactive Mode

```bash
python inference.py \
    --base_model gpt2 \
    --lora_model ./my_finetuned_model \
    --interactive
```

### Single Prompt

```bash
python inference.py \
    --base_model gpt2 \
    --lora_model ./my_finetuned_model \
    --prompt "Your question here" \
    --max_length 200
```

## 📊 Training Parameters Explained

- `--num_epochs`: Number of times to go through the entire dataset (default: 3)
- `--batch_size`: Number of samples per training step (default: 4)
- `--learning_rate`: How fast the model learns (default: 2e-4)
- `--lora_r`: LoRA rank, higher = more parameters but better quality (default: 8)
- `--lora_alpha`: LoRA scaling factor (default: 16)
- `--max_length`: Maximum sequence length in tokens (default: 512)
- `--gradient_accumulation_steps`: Simulate larger batch sizes (default: 4)

## 💡 Tips for Hackathons

1. **Start Small**: Test with 500 rows first to verify everything works
2. **Monitor Training**: Watch the loss - it should decrease over time
3. **Quick Iterations**: Use fewer epochs (1-2) for rapid testing
4. **GPU Memory Issues**: 
   - Reduce `--batch_size` to 1 or 2
   - Use `--use_8bit` flag
   - Reduce `--max_length` to 256
5. **Better Results**:
   - More epochs (5-10) if you have time
   - Increase `--lora_r` to 16 or 32
   - Clean and format your data well

## 📈 Expected Training Time

On a typical GPU (e.g., RTX 3060):
- 5000 rows, 3 epochs, batch_size=4: ~20-30 minutes
- 5000 rows, 1 epoch, batch_size=4: ~7-10 minutes

On CPU (not recommended but possible):
- Much slower, could take hours

## 🐛 Troubleshooting

**Out of Memory Error:**
```bash
# Try these in order:
python train_lora.py --csv_path data.csv --batch_size 2
python train_lora.py --csv_path data.csv --batch_size 1 --use_8bit
python train_lora.py --csv_path data.csv --batch_size 1 --use_8bit --max_length 256
```

**Model not generating well:**
- Train for more epochs
- Increase LoRA rank (`--lora_r 16`)
- Check your data quality
- Adjust temperature in inference (`--temperature 0.8`)

**CSV format errors:**
- Run validation: `python prepare_dataset.py --csv_path data.csv --validate`
- Ensure proper column names
- Check for missing values

## 📁 Project Structure

```
HACKMAN_Project/
├── train_lora.py           # Main training script
├── inference.py            # Inference/testing script
├── prepare_dataset.py      # Dataset utilities
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── your_data.csv          # Your training data
└── lora_finetuned_model/  # Output directory (created after training)
    ├── adapter_config.json
    ├── adapter_model.bin
    └── ...
```

## 🎓 Learn More

- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [Hugging Face PEFT](https://huggingface.co/docs/peft)
- [Transformers Documentation](https://huggingface.co/docs/transformers)

## 🏆 Hackathon Tips

1. **Demo Ready**: Keep your inference script ready with sample prompts
2. **Metrics**: Note training loss and time for your presentation
3. **Comparison**: Show before/after examples (base model vs fine-tuned)
4. **Scalability**: Mention LoRA's efficiency (95%+ parameter reduction)

## 📝 Quick Start Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Prepare your CSV dataset
- [ ] Validate dataset: `python prepare_dataset.py --csv_path data.csv`
- [ ] Start training: `python train_lora.py --csv_path data.csv`
- [ ] Test model: `python inference.py --interactive`
- [ ] Prepare demo prompts
- [ ] Document your results

Good luck with your hackathon! 🚀
