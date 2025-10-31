# 🎓 MCP Quick Start - Student Edition

**Generate unlimited synthetic data with GitHub Student Pro!** No API costs, no rate limits!

## ⚡ Fast Track (5 Minutes)

### Prerequisites
- ✅ GitHub Student Pro (or Copilot subscription)
- ✅ VS Code + GitHub Copilot extension
- ✅ Node.js 18+
- ✅ Python 3.11+
- ✅ Docker

### Step 1: Build MCP Server
```bash
cd /home/neonpulse/Dev/codezz/hackthons/synthaix/mcp-server
npm install && npm run build
```

### Step 2: Configure VS Code
Add to VS Code `settings.json`:
```json
{
  "mcp.servers": {
    "synthaix": {
      "command": "node",
      "args": ["/home/neonpulse/Dev/codezz/hackthons/synthaix/mcp-server/dist/index.js"]
    }
  }
}
```
**Replace path with your actual path!** Then restart VS Code.

### Step 3: Test MCP
```bash
python test_mcp.py
```
Expected: `✅ All tests completed!`

### Step 4: Start System
```bash
docker-compose up -d
```

### Step 5: Generate Data!
1. Open: **http://localhost:8501**
2. Enter: `"user data with name, email, age"`
3. Generate: `10000` rows
4. Download CSV!

## 🎉 Done!

You now have **unlimited** data generation with $0 costs!

Read full guide: `QUICKSTART.md`
Architecture details: `docs/MCP_ARCHITECTURE.md`

---
**Perfect for hackathons!** 🏆
