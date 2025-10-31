#!/bin/bash

# SynthAIx Project Verification Script
# Checks that all components are properly set up

echo "🔍 SynthAIx Project Verification"
echo "================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Helper functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. Checking Directory Structure..."
echo "-----------------------------------"

# Check main directories
[ -d "backend" ] && check_pass "backend/" || check_fail "backend/"
[ -d "frontend" ] && check_pass "frontend/" || check_fail "frontend/"
[ -d "docs" ] && check_pass "docs/" || check_fail "docs/"
[ -d "tests" ] && check_pass "tests/" || check_fail "tests/"
[ -d "examples" ] && check_pass "examples/" || check_fail "examples/"

echo ""
echo "2. Checking Backend Files..."
echo "----------------------------"

# Check backend structure
[ -f "backend/Dockerfile" ] && check_pass "backend/Dockerfile" || check_fail "backend/Dockerfile"
[ -f "backend/requirements.txt" ] && check_pass "backend/requirements.txt" || check_fail "backend/requirements.txt"
[ -f "backend/app/main.py" ] && check_pass "backend/app/main.py" || check_fail "backend/app/main.py"
[ -f "backend/app/core/config.py" ] && check_pass "backend/app/core/config.py" || check_fail "backend/app/core/config.py"
[ -f "backend/app/api/routes.py" ] && check_pass "backend/app/api/routes.py" || check_fail "backend/app/api/routes.py"
[ -f "backend/app/agents/orchestrator.py" ] && check_pass "backend/app/agents/orchestrator.py" || check_fail "backend/app/agents/orchestrator.py"
[ -f "backend/app/agents/generator.py" ] && check_pass "backend/app/agents/generator.py" || check_fail "backend/app/agents/generator.py"
[ -f "backend/app/tools/deduplication.py" ] && check_pass "backend/app/tools/deduplication.py" || check_fail "backend/app/tools/deduplication.py"

echo ""
echo "3. Checking Frontend Files..."
echo "-----------------------------"

# Check frontend structure
[ -f "frontend/Dockerfile" ] && check_pass "frontend/Dockerfile" || check_fail "frontend/Dockerfile"
[ -f "frontend/requirements.txt" ] && check_pass "frontend/requirements.txt" || check_fail "frontend/requirements.txt"
[ -f "frontend/app.py" ] && check_pass "frontend/app.py" || check_fail "frontend/app.py"
[ -f "frontend/components/visualizations.py" ] && check_pass "frontend/components/visualizations.py" || check_fail "frontend/components/visualizations.py"
[ -f "frontend/utils/api_client.py" ] && check_pass "frontend/utils/api_client.py" || check_fail "frontend/utils/api_client.py"

echo ""
echo "4. Checking Docker Configuration..."
echo "-----------------------------------"

[ -f "docker-compose.yml" ] && check_pass "docker-compose.yml" || check_fail "docker-compose.yml"
[ -f ".env.example" ] && check_pass ".env.example" || check_fail ".env.example"
[ -f ".gitignore" ] && check_pass ".gitignore" || check_fail ".gitignore"

echo ""
echo "5. Checking Documentation..."
echo "----------------------------"

[ -f "README.md" ] && check_pass "README.md" || check_fail "README.md"
[ -f "QUICKSTART.md" ] && check_pass "QUICKSTART.md" || check_fail "QUICKSTART.md"
[ -f "docs/API.md" ] && check_pass "docs/API.md" || check_fail "docs/API.md"
[ -f "docs/DEPLOYMENT.md" ] && check_pass "docs/DEPLOYMENT.md" || check_fail "docs/DEPLOYMENT.md"
[ -f "CONTRIBUTING.md" ] && check_pass "CONTRIBUTING.md" || check_fail "CONTRIBUTING.md"
[ -f "CHANGELOG.md" ] && check_pass "CHANGELOG.md" || check_fail "CHANGELOG.md"
[ -f "PROJECT_STRUCTURE.md" ] && check_pass "PROJECT_STRUCTURE.md" || check_fail "PROJECT_STRUCTURE.md"
[ -f "ARCHITECTURE.md" ] && check_pass "ARCHITECTURE.md" || check_fail "ARCHITECTURE.md"

echo ""
echo "6. Checking Scripts & Utilities..."
echo "----------------------------------"

[ -f "start.sh" ] && check_pass "start.sh" || check_fail "start.sh"
[ -f "setup-dev.sh" ] && check_pass "setup-dev.sh" || check_fail "setup-dev.sh"
[ -f "Makefile" ] && check_pass "Makefile" || check_fail "Makefile"
[ -x "start.sh" ] && check_pass "start.sh is executable" || check_warn "start.sh not executable"
[ -x "setup-dev.sh" ] && check_pass "setup-dev.sh is executable" || check_warn "setup-dev.sh not executable"

echo ""
echo "7. Checking Examples..."
echo "-----------------------"

[ -f "examples/python_client.py" ] && check_pass "examples/python_client.py" || check_fail "examples/python_client.py"
[ -f "examples/data_science_workflow.py" ] && check_pass "examples/data_science_workflow.py" || check_fail "examples/data_science_workflow.py"
[ -f "examples/README.md" ] && check_pass "examples/README.md" || check_fail "examples/README.md"

echo ""
echo "8. Checking Tests..."
echo "-------------------"

[ -f "tests/test_backend.py" ] && check_pass "tests/test_backend.py" || check_fail "tests/test_backend.py"
[ -f "pyproject.toml" ] && check_pass "pyproject.toml" || check_fail "pyproject.toml"

echo ""
echo "9. Checking Configuration Files..."
echo "----------------------------------"

# Check if .env exists
if [ -f ".env" ]; then
    check_pass ".env exists"
    
    # Check if OPENAI_API_KEY is set
    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        check_pass "OPENAI_API_KEY is set"
    else
        check_warn "OPENAI_API_KEY not set in .env"
    fi
else
    check_warn ".env not found (use .env.example to create)"
fi

echo ""
echo "10. Checking Python Syntax..."
echo "-----------------------------"

# Check Python files for syntax errors
python_errors=0

for file in backend/app/**/*.py frontend/**/*.py examples/*.py; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            continue
        else
            check_fail "Syntax error in $file"
            ((python_errors++))
        fi
    fi
done

if [ $python_errors -eq 0 ]; then
    check_pass "No Python syntax errors"
fi

echo ""
echo "11. Checking Docker..."
echo "---------------------"

if command -v docker &> /dev/null; then
    check_pass "Docker is installed"
    
    if docker info &> /dev/null; then
        check_pass "Docker is running"
    else
        check_warn "Docker is not running"
    fi
else
    check_fail "Docker is not installed"
fi

if command -v docker-compose &> /dev/null; then
    check_pass "Docker Compose is installed"
else
    check_fail "Docker Compose is not installed"
fi

echo ""
echo "================================="
echo "📊 Verification Summary"
echo "================================="
echo ""
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

TOTAL=$((PASSED + FAILED))
SUCCESS_RATE=$((PASSED * 100 / TOTAL))

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Project is ready.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Ensure .env file has OPENAI_API_KEY"
    echo "2. Run: docker-compose up -d"
    echo "3. Access: http://localhost:8501"
    exit 0
else
    echo -e "${RED}⚠️  Some checks failed. Please review above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "• Run: chmod +x start.sh setup-dev.sh"
    echo "• Copy: cp .env.example .env"
    echo "• Check: File paths and names"
    exit 1
fi
