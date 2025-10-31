# 🚀 Quick Start Guide - SynthAIx

Get SynthAIx up and running in under 5 minutes!

## Prerequisites Checklist

Before you begin, ensure you have:

- [ ] **Docker Desktop** installed and running
- [ ] **OpenAI API Key** from https://platform.openai.com/api-keys
- [ ] **4GB RAM** available
- [ ] **10GB disk space** available
- [ ] **Internet connection** for pulling images

## 📦 Installation (3 Steps)

### Step 1: Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd synthaix

# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

**Important**: Replace `your_openai_api_key_here` with your actual API key:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 2: Start the Application

```bash
# Make start script executable (Linux/Mac)
chmod +x start.sh

# Run the start script
./start.sh
```

**Or manually:**
```bash
docker-compose up -d
```

### Step 3: Access the Application

Open your browser and navigate to:
- **Frontend UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Backend API**: http://localhost:8000

## 🎯 Your First Data Generation

### Using the Web Interface

1. **Open Frontend**: Go to http://localhost:8501

2. **Step 1 - Describe Your Data**:
   ```
   Generate financial transactions with date, amount, merchant name, and category
   ```
   Click "🚀 Generate Schema"

3. **Step 2 - Confirm Schema**:
   - Review the AI-generated schema
   - Edit if needed
   - Set total rows: 1000
   - Click "✅ Confirm & Generate"

4. **Step 3 - Watch Progress**:
   - View real-time progress bar
   - Monitor chunk completion
   - See agent statistics

5. **Step 4 - Download Results**:
   - Preview generated data
   - Download as CSV, JSON, or Excel

### Using the API

```bash
# 1. Translate schema
curl -X POST "http://localhost:8000/api/v1/schema/translate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Generate user records with name and email"}'

# 2. Generate data (use schema from step 1)
curl -X POST "http://localhost:8000/api/v1/data/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "schema": {
      "fields": [
        {"name": "name", "type": "string"},
        {"name": "email", "type": "email"}
      ]
    },
    "total_rows": 100,
    "enable_deduplication": true
  }'

# 3. Check status (use job_id from step 2)
curl "http://localhost:8000/api/v1/jobs/{job_id}/status"
```

## 🔧 Troubleshooting

### Backend Won't Start

**Problem**: Backend container fails to start

**Solution**:
```bash
# Check logs
docker-compose logs backend

# Common fixes:
# 1. Verify OpenAI API key is set
docker-compose exec backend env | grep OPENAI_API_KEY

# 2. Restart Redis
docker-compose restart redis

# 3. Rebuild containers
docker-compose down
docker-compose up -d --build
```

### Frontend Can't Connect

**Problem**: Frontend shows "Backend: Offline"

**Solution**:
```bash
# 1. Verify backend is running
curl http://localhost:8000/api/v1/health

# 2. Check network
docker-compose exec frontend ping backend

# 3. Restart frontend
docker-compose restart frontend
```

### Port Already in Use

**Problem**: Error: "port is already allocated"

**Solution**:
```bash
# Option 1: Stop conflicting service
sudo lsof -i :8000  # Find process using port 8000
sudo kill -9 <PID>  # Kill the process

# Option 2: Change ports in docker-compose.yml
# Edit ports section:
# ports:
#   - "8001:8000"  # Change 8000 to 8001
```

### Out of Memory

**Problem**: Container crashes with OOM error

**Solution**:
```bash
# Reduce MAX_WORKERS in .env
MAX_WORKERS=10

# Restart services
docker-compose restart backend
```

## 📊 Verify Installation

Run this health check:

```bash
# Check all services
docker-compose ps

# Should see:
# synthaix-backend    running
# synthaix-frontend   running
# synthaix-redis      running

# Test backend
curl http://localhost:8000/api/v1/health
# Should return: {"status":"healthy",...}

# Test frontend
curl http://localhost:8501/_stcore/health
# Should return: {"status":"ok"}
```

## 🛑 Stopping the Application

```bash
# Stop services (keep data)
docker-compose down

# Stop services and remove data
docker-compose down -v
```

## 🔄 Updating

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## 📚 Next Steps

Now that you're up and running:

1. **Explore Examples**: Check `docs/API.md` for more examples
2. **Read Documentation**: See `README.md` for architecture details
3. **Customize**: Edit `.env` to tune performance
4. **Deploy**: See `docs/DEPLOYMENT.md` for production deployment

## 🆘 Need Help?

- **Documentation**: See `README.md` and `docs/`
- **API Reference**: http://localhost:8000/docs
- **Issues**: Create a GitHub issue
- **Logs**: `docker-compose logs -f`

## 💡 Pro Tips

### Faster Generation
```bash
# Increase workers
MAX_WORKERS=30

# Increase chunk size
# Use 1000 for chunks in the frontend
```

### Better Quality
```bash
# Stricter deduplication
SIMILARITY_THRESHOLD=0.90

# Use higher quality model
OPENAI_MODEL=gpt-4
```

### Development Mode
```bash
# Run with live reload
docker-compose up

# View logs in real-time
docker-compose logs -f backend
```

## 📖 Example Use Cases

### E-commerce Data
```
Generate e-commerce orders with order ID, customer name, product name, 
quantity, price, order date, and shipping address
```

### User Records
```
Generate user profiles with username, email, phone number, registration date, 
subscription tier, and account status
```

### IoT Sensor Data
```
Generate IoT sensor readings with device ID, timestamp, temperature, 
humidity, battery level, and GPS coordinates
```

### Financial Transactions
```
Generate financial transactions with transaction ID, date, amount, 
merchant name, category, and user ID
```

---

**🎉 Congratulations!** You're ready to generate synthetic data at scale with SynthAIx!

For advanced configuration and production deployment, see:
- `docs/DEPLOYMENT.md` - Production deployment guide
- `docs/API.md` - Complete API reference
- `README.md` - Full documentation
