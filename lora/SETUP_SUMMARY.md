# HACKMAN_Project - LoRA Fine-tuning Setup ✅

## 📁 Project Structure

```
HACKMAN_Project/
├── train_lora.py              # Main training script
├── inference.py               # Test your fine-tuned model
├── prepare_dataset.py         # Dataset validation tools
├── merge_lora.py              # Merge adapter with base model
├── lora_finetuning.ipynb      # Interactive Jupyter notebook
├── requirements.txt           # Python dependencies
├── config_examples.txt        # Training configuration examples
├── quick_start.sh            # Quick setup script
├── README.md                  # Complete documentation
└── .gitignore                # Git ignore file
```

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
# Option A: Use the quick start script
./quick_start.sh

# Option B: Manual installation
pip install -r requirements.txt
```

### Step 2: Prepare Your Dataset
Place your CSV file in this directory. It should have one of these formats:

**Format A: instruction + response**
```csv
instruction,response
"What is AI?","Artificial Intelligence is..."
```

**Format B: question + answer**
```csv
question,answer
"What is Python?","Python is a programming language..."
```

**Format C: prompt + completion**
```csv
prompt,completion
"Explain quantum","Quantum physics..."
```

**Format D: text only**
```csv
text
"Complete training text here..."
```

Validate your dataset:
```bash
python prepare_dataset.py --csv_path your_data.csv --validate
```

### Step 3: Train!
```bash
# Basic training (recommended for hackathon)
python train_lora.py --csv_path your_data.csv --num_epochs 3

# If you have limited GPU memory
python train_lora.py --csv_path your_data.csv --use_8bit --batch_size 2
```

## 💡 Hackathon Mode (Fast Testing)

```bash
# Quick test with 1 epoch (~10 minutes)
python train_lora.py --csv_path your_data.csv --num_epochs 1 --batch_size 4
```

## 🎮 Testing Your Model

```bash
# Interactive mode
python inference.py --lora_model ./lora_finetuned_model --interactive

# Single prompt
python inference.py \
    --lora_model ./lora_finetuned_model \
    --prompt "Your question here"
```

## 📊 What Gets Created

After training, you'll have:
- `lora_finetuned_model/` - Your fine-tuned model adapter
  - Only ~10-20MB in size (LoRA magic!)
  - Contains adapter weights
  - Can be loaded with the base model

## 🎯 Expected Results

**Training Time (RTX 3060):**
- 5000 rows, 3 epochs: ~20-30 minutes
- 5000 rows, 1 epoch: ~7-10 minutes

**Model Size:**
- Base model: ~500MB
- LoRA adapter: ~10-20MB (95%+ reduction!)

**Performance:**
- Trainable parameters: <5% of total
- Quality: Similar to full fine-tuning
- Inference speed: Same as base model

## 🛠️ Troubleshooting

### Out of Memory Error
```bash
# Try in this order:
python train_lora.py --csv_path data.csv --batch_size 2
python train_lora.py --csv_path data.csv --batch_size 1 --use_8bit
python train_lora.py --csv_path data.csv --batch_size 1 --use_8bit --max_length 256
```

### CSV Format Error
```bash
# Check your dataset format
python prepare_dataset.py --csv_path your_data.csv --validate

# See required formats in README.md
```

### Slow Training
- Reduce `--num_epochs` to 1-2 for quick testing
- Ensure you're using GPU: check with `torch.cuda.is_available()`
- Use smaller `--max_length` (e.g., 256 instead of 512)

## 📚 Files Explained

1. **train_lora.py** - Main training script with full control
2. **inference.py** - Test your model after training
3. **prepare_dataset.py** - Validate and analyze your CSV
4. **lora_finetuning.ipynb** - Interactive notebook (great for exploration)
5. **merge_lora.py** - Combine adapter with base model (optional)
6. **config_examples.txt** - Pre-configured training commands

## 🎓 Key Concepts

**LoRA (Low-Rank Adaptation):**
- Trains only 1-5% of model parameters
- Saves memory and time
- Nearly same quality as full fine-tuning
- Creates small adapter files (~10-20MB)

**Parameters:**
- `num_epochs`: How many times to train on full dataset
- `batch_size`: Samples per step (lower = less memory)
- `learning_rate`: How fast model learns (2e-4 is good default)
- `lora_r`: Rank (8 = standard, 16 = higher quality)

## 🏆 Demo Tips

1. **Before/After Comparison**
   - Show base model output
   - Show fine-tuned model output
   - Highlight improvements

2. **Key Metrics to Mention**
   - Training time: ~20 minutes
   - Dataset size: 5000 rows
   - Parameter reduction: 95%+
   - Model size: Only 10-20MB adapter

3. **Live Demo**
   - Use `inference.py --interactive`
   - Prepare 3-5 interesting prompts
   - Show various capabilities

4. **Technical Highlights**
   - LoRA efficiency
   - Fast iteration time
   - Deployable on consumer hardware

## ⚡ Advanced Usage

### Train with Weights & Biases Logging
```bash
python train_lora.py --csv_path data.csv --use_wandb
```

### Use Different Base Model
```bash
# Larger model (needs more memory)
python train_lora.py \
    --csv_path data.csv \
    --model_name microsoft/phi-1_5 \
    --use_8bit
```

### High Quality Training
```bash
python train_lora.py \
    --csv_path data.csv \
    --num_epochs 5 \
    --lora_r 16 \
    --lora_alpha 32
```

### Merge Adapter with Base Model
```bash
python merge_lora.py \
    --base_model gpt2 \
    --lora_model ./lora_finetuned_model \
    --output ./merged_model
```

## 📝 Checklist for Hackathon

- [ ] Install dependencies (`./quick_start.sh`)
- [ ] Validate dataset (`python prepare_dataset.py --csv_path data.csv`)
- [ ] Quick test training (1 epoch to verify)
- [ ] Full training (3-5 epochs)
- [ ] Test with inference script
- [ ] Prepare demo prompts
- [ ] Note key metrics (time, loss, size)
- [ ] Create before/after examples
- [ ] Practice demo presentation

## 🎯 Resources

- See `README.md` for complete documentation
- Check `config_examples.txt` for training recipes
- Try `lora_finetuning.ipynb` for interactive exploration
- Read comments in `train_lora.py` for customization

## 🆘 Need Help?

Common issues and solutions are in `README.md`

For more details, check the individual Python files - they have extensive comments!

---

**Ready to go? Start with:**
```bash
python train_lora.py --csv_path your_data.csv
```

Good luck with your hackathon! 🚀
