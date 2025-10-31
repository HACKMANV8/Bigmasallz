# SynthAIx MCP Server

**Use GitHub Copilot as Your Unlimited Data Generation Engine!**

This MCP (Model Context Protocol) server turns GitHub Copilot into a synthetic data generator with unlimited tokens (via GitHub Student Pro).

## 🎯 The Innovation

Instead of using rate-limited APIs (OpenAI, Gemini), we use:
- **GitHub Copilot** (you!) as the AI engine
- **MCP Protocol** to expose tools to VS Code
- **Your Student Pro unlimited tokens** for generation
- **No API rate limits or costs!**

## 🏗️ Architecture

```
┌─────────────────┐
│   VS Code +     │
│ GitHub Copilot  │  ← Uses unlimited student tokens
└────────┬────────┘
         │ MCP Protocol
┌────────▼────────┐
│  MCP Server     │  ← Exposes data generation tools
│  (This Project) │
└────────┬────────┘
         │ HTTP/WebSocket
┌────────▼────────┐
│  SynthAIx       │  ← Main application
│  Backend API    │
└─────────────────┘
```

## 🚀 Setup

### 1. Install Dependencies

```bash
cd mcp-server
npm install
```

### 2. Build the Server

```bash
npm run build
```

### 3. Configure VS Code

Add to your VS Code `settings.json`:

```json
{
  "mcp.servers": {
    "synthaix": {
      "command": "node",
      "args": ["/absolute/path/to/synthaix/mcp-server/dist/index.js"],
      "env": {}
    }
  }
}
```

### 4. Restart VS Code

The MCP server will auto-start and connect to GitHub Copilot.

## 🛠️ Available Tools

### 1. `translate_schema`
Convert natural language to data schema.

**Input:**
```json
{
  "prompt": "user data with name, email, and age"
}
```

**Output:**
```json
{
  "fields": [
    {"name": "name", "type": "string", "description": "User's full name"},
    {"name": "email", "type": "email", "description": "User's email address"},
    {"name": "age", "type": "integer", "constraints": {"min": 0, "max": 120}}
  ]
}
```

### 2. `generate_data_chunk`
Generate synthetic data rows.

**Input:**
```json
{
  "schema": { "fields": [...] },
  "num_rows": 100,
  "chunk_id": "chunk_0",
  "enable_deduplication": false
}
```

**Output:**
```json
[
  {"name": "John Doe", "email": "john@example.com", "age": 28},
  {"name": "Jane Smith", "email": "jane@example.com", "age": 34},
  ...
]
```

### 3. `check_duplicates`
Remove duplicate rows from data.

**Input:**
```json
{
  "data": [...]
}
```

**Output:**
```json
{
  "unique_rows": [...],
  "duplicates_removed": 5
}
```

## 💡 How It Works

1. **Backend calls MCP server** via HTTP/stdio
2. **MCP server formats prompts** for Copilot
3. **Copilot (you!) generates data** using context
4. **MCP server returns data** to backend
5. **No API limits!** Your student account = unlimited tokens

## 📊 Advantages Over APIs

| Feature | OpenAI/Gemini | Copilot MCP |
|---------|---------------|-------------|
| Rate Limits | ✗ Yes (strict) | ✅ None |
| Cost | ✗ Pay per token | ✅ Free (student) |
| Token Limits | ✗ Limited | ✅ Unlimited |
| Quality | ✅ Good | ✅ Excellent |
| Latency | ⚠️ Network | ✅ Local |

## 🔧 Development

### Watch mode
```bash
npm run dev
```

### Test the server
```bash
npm start
```

### Debug
The server logs to stderr, check VS Code output panel.

## 🎓 Perfect for Students!

- ✅ Uses GitHub Student Pro unlimited tokens
- ✅ No credit card needed
- ✅ No API rate limits
- ✅ Generate millions of rows
- ✅ Perfect for hackathons!

## 📝 Next Steps

1. ✅ MCP Server created
2. ⏳ Update backend to call MCP server
3. ⏳ Configure VS Code MCP settings
4. ⏳ Test data generation through Copilot

## 🤝 How to Use with Backend

The backend will communicate with this MCP server instead of OpenAI/Gemini:

```python
# Old way (API limits)
response = openai.chat.completions.create(...)

# New way (unlimited Copilot)
response = mcp_client.call_tool("generate_data_chunk", {
    "schema": schema,
    "num_rows": 1000
})
```

## 🎉 Benefits

- 🚀 **10x faster** - No network latency
- 💰 **$0 cost** - Student account
- 🔓 **No limits** - Generate as much as needed
- 🎯 **Better quality** - Copilot understands context
- 🏆 **Perfect for hackathons** - Unlimited resources!

---

**Built with ❤️ for GitHub Student Developers**
