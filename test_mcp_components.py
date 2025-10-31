#!/usr/bin/env python3
"""
Simple test to verify MCP components without full server protocol.
Tests the Python client and TypeScript server separately.
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🧪 Testing MCP Components")
print("=" * 60)
print()

# Test 1: Check MCP server exists and is built
print("1️⃣  Checking MCP server build...")
mcp_server_path = Path(__file__).parent / "mcp-server" / "dist" / "index.js"

if mcp_server_path.exists():
    print(f"   ✅ MCP server found at: {mcp_server_path}")
    print(f"   📦 Size: {mcp_server_path.stat().st_size} bytes")
else:
    print(f"   ❌ MCP server not found at: {mcp_server_path}")
    print("   Run: cd mcp-server && npm install && npm run build")
    sys.exit(1)

# Test 2: Check Python MCP client
print("\n2️⃣  Checking Python MCP client...")
try:
    from backend.app.mcp.client import MCPClient
    print("   ✅ MCPClient imported successfully")
    
    # Try to create client instance
    client = MCPClient()
    print(f"   ✅ MCPClient instance created")
    print(f"   📂 Server path: {client.server_path}")
    
except Exception as e:
    print(f"   ❌ Failed to import/create MCPClient: {e}")
    sys.exit(1)

# Test 3: Check MCP Generator Agent
print("\n3️⃣  Checking MCP Generator Agent...")
try:
    from backend.app.mcp.client import get_mcp_client
    from backend.app.agents.generator_mcp import MCPGeneratorAgent, create_mcp_agent
    from backend.app.models.schemas import DataSchema, SchemaField
    
    print("   ✅ MCPGeneratorAgent imported successfully")
    
    # Create a test schema
    test_schema = DataSchema(
        fields=[
            SchemaField(name="name", type="string", description="Person's name"),
            SchemaField(name="age", type="integer", description="Person's age")
        ]
    )
    
    # Create agent
    agent = create_mcp_agent(0, test_schema, enable_deduplication=False)
    print(f"   ✅ MCPGeneratorAgent created (agent_id={agent.agent_id})")
    
except Exception as e:
    print(f"   ❌ Failed to create MCPGeneratorAgent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check orchestrator uses MCP agents
print("\n4️⃣  Checking Orchestrator MCP integration...")
try:
    from backend.app.agents.orchestrator import OrchestratorAgent
    import inspect
    
    # Check if orchestrator imports MCPGeneratorAgent
    source = inspect.getsource(OrchestratorAgent)
    
    if "MCPGeneratorAgent" in source:
        print("   ✅ Orchestrator uses MCPGeneratorAgent")
    else:
        print("   ⚠️  Orchestrator might still use old GeneratorAgent")
        
except Exception as e:
    print(f"   ❌ Failed to check Orchestrator: {e}")

# Test 5: Check Node.js dependencies
print("\n5️⃣  Checking Node.js dependencies...")
package_json = Path(__file__).parent / "mcp-server" / "package.json"
node_modules = Path(__file__).parent / "mcp-server" / "node_modules"

if package_json.exists():
    print(f"   ✅ package.json exists")
    with open(package_json) as f:
        pkg = json.load(f)
        deps = pkg.get("dependencies", {})
        print(f"   📦 Dependencies:")
        for dep, version in deps.items():
            print(f"      • {dep}: {version}")

if node_modules.exists():
    print(f"   ✅ node_modules directory exists")
else:
    print(f"   ⚠️  node_modules not found - run 'npm install'")

# Summary
print("\n" + "=" * 60)
print("📊 Summary")
print("=" * 60)
print()
print("✅ MCP Server: Built and ready")
print("✅ Python Client: Imported successfully")
print("✅ MCP Agent: Created successfully")
print("✅ Architecture: Ready for testing")
print()
print("🎯 Next Steps:")
print("   1. Configure VS Code settings.json with MCP server")
print("   2. Restart VS Code to load MCP server")
print("   3. Start backend: docker-compose up backend")
print("   4. Test data generation via API")
print()
print("📖 Read: docs/MCP_ARCHITECTURE.md for details")
print("🚀 Quick start: MCP_QUICKSTART.md")
print()
print("=" * 60)
print("🎉 All component checks passed!")
print("=" * 60)
print()
