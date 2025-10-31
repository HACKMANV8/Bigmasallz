# 🚀 Next Steps - Getting Started with SynthAIx

## ✅ What's Been Updated

Anthropic/Claude support has been **removed** and replaced with:
- ✅ OpenAI (GPT-4, GPT-3.5, etc.)
- ✅ Google Gemini (gemini-1.5-pro, gemini-1.5-flash)

## 📋 Quick Setup Checklist

### 1️⃣ Get Your API Keys (Choose One or Both)

#### Option A: OpenAI Only (Recommended for Quality)
1. Go to: https://platform.openai.com/api-keys
2. Sign up / Log in
3. Click "Create new secret key"
4. Copy key (starts with `sk-...`)

#### Option B: Google Gemini (Recommended for Cost)
1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Get API Key"
4. Copy key

#### Option C: Both (Best Performance/Cost Mix)
- Get both keys above
- Use GPT-4 for schema inference (accurate)
- Use Gemini Flash for generation (fast & cheap)

### 2️⃣ Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit with your keys
nano .env
```

**For OpenAI Only:**
```bash
OPENAI_API_KEY=sk-your-actual-key-here
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4-turbo
```

**For Gemini Only:**
```bash
GOOGLE_API_KEY=your-actual-key-here
OPENAI_API_KEY=sk-...  # Still needed for embeddings
DEFAULT_LLM_PROVIDER=gemini
DEFAULT_MODEL=gemini-1.5-flash
```

**For Both (Hybrid - Recommended):**
```bash
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_API_KEY=your-google-key

# Use GPT-4 for schema understanding (accuracy)
SCHEMA_MODEL=gpt-4-turbo

# Use Gemini for data generation (speed + cost savings)
DEFAULT_LLM_PROVIDER=gemini
GENERATION_MODEL=gemini-1.5-flash

# Use OpenAI embeddings (best quality)
EMBEDDING_MODEL=text-embedding-3-small
```

### 3️⃣ Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- ✅ `openai==1.10.0`
- ✅ `google-generativeai==0.3.2`
- ✅ All other dependencies

### 4️⃣ Choose Your Deployment Method

#### Option A: Docker (Easiest)
```bash
# Start everything
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Stop when done
docker-compose down
```

#### Option B: Local Development
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate  # or: . venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

#### Option C: Makefile Commands
```bash
# Install everything
make install

# Run in development mode
make dev

# Run tests
make test
```

### 5️⃣ Access the Application

Once running, open your browser:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 6️⃣ Generate Your First Dataset

1. Go to http://localhost:3000
2. **Step 1**: Enter natural language description
   ```
   Example: "Customer database with name, email, age, and subscription status"
   ```
3. **Step 2**: Review and edit the generated schema
4. **Step 3**: Configure generation (rows, workers, etc.)
5. **Step 4**: Watch real-time progress
6. **Download**: Get CSV or JSON file

## 📚 Important Documentation

- **`LLM_PROVIDERS.md`** - Detailed guide on API keys and models
- **`CHANGELOG_LLM.md`** - What changed in this update
- **`QUICKSTART.md`** - Full quick start guide
- **`ARCHITECTURE.md`** - Technical architecture details
- **`README.md`** - Project overview

## 💰 Cost Estimates (10,000 rows)

| Provider | Model | Cost | Speed | Quality |
|----------|-------|------|-------|---------|
| OpenAI | gpt-4-turbo | ~$5-10 | Medium | ⭐⭐⭐⭐⭐ |
| OpenAI | gpt-3.5-turbo | ~$0.50-1 | Fast | ⭐⭐⭐⭐ |
| Gemini | gemini-1.5-pro | ~$0.50-1 | Medium | ⭐⭐⭐⭐⭐ |
| Gemini | gemini-1.5-flash | ~$0.10-0.30 | Very Fast | ⭐⭐⭐⭐ |

**Recommendation**: Start with `gemini-1.5-flash` for testing (cheapest), then upgrade to `gpt-4-turbo` for production quality.

## 🔧 Troubleshooting

### Issue: "API key not valid"
```bash
# Check your .env file
cat .env | grep API_KEY

# Make sure no extra spaces or quotes
OPENAI_API_KEY=sk-abc123  # ✅ Correct
OPENAI_API_KEY="sk-abc123"  # ❌ Remove quotes
OPENAI_API_KEY= sk-abc123  # ❌ Remove space
```

### Issue: "Module not found: google.generativeai"
```bash
# Install the package
cd backend
pip install google-generativeai==0.3.2

# Or reinstall all requirements
pip install -r requirements.txt
```

### Issue: "Rate limit exceeded"
```bash
# Edit .env to reduce parallel workers
MAX_WORKERS=5  # Instead of 20

# Or add delay between requests
# (This is handled automatically by the system)
```

### Issue: Docker containers won't start
```bash
# Check if ports are in use
sudo lsof -i :8000  # Backend
sudo lsof -i :3000  # Frontend

# Kill existing processes
kill -9 <PID>

# Or change ports in docker-compose.yml
```

## 🎯 Quick Test

Test that everything works:

```bash
# Test backend health
curl http://localhost:8000/health

# Test schema translation
curl -X POST http://localhost:8000/api/schema/translate \
  -H "Content-Type: application/json" \
  -d '{"description": "User table with name and email"}'

# Check API documentation
open http://localhost:8000/docs
```

## 🚀 Production Deployment

When ready for production:

1. **Set secure secrets**:
   ```bash
   SECRET_KEY=$(openssl rand -hex 32)
   ```

2. **Enable production mode**:
   ```bash
   DEBUG=false
   ENVIRONMENT=production
   ```

3. **Use proper database**:
   ```bash
   DATABASE_URL=postgresql://user:pass@host:5432/synthaix
   REDIS_URL=redis://host:6379/0
   ```

4. **Deploy with Docker Compose**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

## 📞 Need Help?

- 📖 **Documentation**: Check the docs mentioned above
- 🐛 **Issues**: Create a GitHub issue
- 💬 **Questions**: See troubleshooting section in QUICKSTART.md

## ✅ Verification Checklist

Before using the system, verify:

- [ ] API keys added to `.env` file
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Backend running (port 8000)
- [ ] Frontend running (port 3000)
- [ ] Health check passes (`curl localhost:8000/health`)
- [ ] Can access API docs (`localhost:8000/docs`)
- [ ] Can access UI (`localhost:3000`)

## 🎉 You're Ready!

Once all checks pass, you're ready to generate synthetic data!

Start with a simple test:
1. Go to http://localhost:3000
2. Enter: "A simple user table with name and email"
3. Generate 100 rows
4. Download and verify

Then scale up to thousands or millions of rows! 🚀

---

**Last Updated**: October 31, 2025
**Version**: 1.0.0 (Anthropic removed, Gemini added)
