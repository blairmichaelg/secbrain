#!/bin/bash
# Quick start script for running SecBrain against Threshold Network
# Usage: ./run-threshold.sh [dry-run|full|critical]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCOPE="$SCRIPT_DIR/scope.yaml"
PROGRAM="$SCRIPT_DIR/program.json"
WORKSPACE="$SCRIPT_DIR/workspace"

# Check for mode argument
MODE="${1:-dry-run}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SecBrain - Threshold Network${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Validate configuration first
echo -e "${YELLOW}Step 1: Validating configuration...${NC}"
if ! secbrain validate --scope "$SCOPE" --program "$PROGRAM"; then
    echo -e "${RED}Configuration validation failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Configuration valid${NC}"
echo ""

# Check API keys
echo -e "${YELLOW}Step 2: Checking API keys...${NC}"
API_KEYS_OK=true

if [ -z "$PERPLEXITY_API_KEY" ]; then
    echo -e "${RED}✗ PERPLEXITY_API_KEY not set${NC}"
    API_KEYS_OK=false
else
    echo -e "${GREEN}✓ PERPLEXITY_API_KEY set${NC}"
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    echo -e "${RED}✗ GOOGLE_API_KEY not set${NC}"
    API_KEYS_OK=false
else
    echo -e "${GREEN}✓ GOOGLE_API_KEY set${NC}"
fi

# Check for at least one worker model key
if [ -z "$TOGETHER_API_KEY" ] && [ -z "$OPENROUTER_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}✗ No worker model API key set (need TOGETHER_API_KEY, OPENROUTER_API_KEY, or OPENAI_API_KEY)${NC}"
    API_KEYS_OK=false
else
    if [ -n "$TOGETHER_API_KEY" ]; then
        echo -e "${GREEN}✓ TOGETHER_API_KEY set (recommended)${NC}"
    elif [ -n "$OPENROUTER_API_KEY" ]; then
        echo -e "${GREEN}✓ OPENROUTER_API_KEY set${NC}"
    elif [ -n "$OPENAI_API_KEY" ]; then
        echo -e "${GREEN}✓ OPENAI_API_KEY set${NC}"
    fi
fi

if [ "$API_KEYS_OK" = false ]; then
    echo ""
    echo -e "${YELLOW}API keys are missing. For dry-run mode, you can continue without them.${NC}"
    echo -e "${YELLOW}For full analysis, please set the required API keys:${NC}"
    echo ""
    echo "export PERPLEXITY_API_KEY=pplx-xxxx"
    echo "export GOOGLE_API_KEY=AIza-xxxx"
    echo "export TOGETHER_API_KEY=your-key  # Recommended"
    echo ""
    if [ "$MODE" != "dry-run" ]; then
        echo -e "${RED}Cannot proceed with full analysis without API keys${NC}"
        exit 1
    fi
fi
echo ""

# Display run configuration
echo -e "${YELLOW}Step 3: Run Configuration${NC}"
echo "  Scope: $SCOPE"
echo "  Program: $PROGRAM"
echo "  Workspace: $WORKSPACE"
echo "  Mode: $MODE"
echo ""

# Run based on mode
case "$MODE" in
    dry-run)
        echo -e "${YELLOW}Step 4: Running DRY-RUN analysis...${NC}"
        echo "This will validate the setup without making real API calls."
        echo ""
        secbrain run \
            --scope "$SCOPE" \
            --program "$PROGRAM" \
            --workspace "$WORKSPACE" \
            --dry-run
        ;;
    
    full)
        echo -e "${YELLOW}Step 4: Running FULL analysis...${NC}"
        echo "This will analyze all 39 contracts and make real API calls."
        echo -e "${RED}WARNING: This will incur API costs (estimated $10-30).${NC}"
        echo ""
        read -p "Continue? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cancelled."
            exit 0
        fi
        
        secbrain run \
            --scope "$SCOPE" \
            --program "$PROGRAM" \
            --workspace "$WORKSPACE"
        ;;
    
    critical)
        echo -e "${YELLOW}Step 4: Running CRITICAL contracts analysis...${NC}"
        echo "This will analyze only high-value contracts (TBTC, Bridge, Staking)."
        echo ""
        
        # Check if critical scope exists
        CRITICAL_SCOPE="$SCRIPT_DIR/scope-critical.yaml"
        if [ ! -f "$CRITICAL_SCOPE" ]; then
            echo -e "${RED}Critical scope file not found: $CRITICAL_SCOPE${NC}"
            echo "Please create it with high-value contracts only."
            exit 1
        fi
        
        secbrain run \
            --scope "$CRITICAL_SCOPE" \
            --program "$PROGRAM" \
            --workspace "$WORKSPACE-critical"
        ;;
    
    *)
        echo -e "${RED}Invalid mode: $MODE${NC}"
        echo "Usage: $0 [dry-run|full|critical]"
        echo ""
        echo "Modes:"
        echo "  dry-run  - Validate setup without API calls (default)"
        echo "  full     - Analyze all 39 contracts"
        echo "  critical - Analyze only critical contracts"
        exit 1
        ;;
esac

# Generate insights if workspace exists and has data
if [ -d "$WORKSPACE" ] && [ -f "$WORKSPACE/run_summary.json" ]; then
    echo ""
    echo -e "${YELLOW}Step 5: Generate insights report? (y/N)${NC}"
    read -p "" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Generating insights...${NC}"
        secbrain insights --workspace "$WORKSPACE" --format html --open || true
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Run complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Workspace: $WORKSPACE"
echo ""
echo "Next steps:"
echo "1. Review logs: $WORKSPACE/logs/"
echo "2. Check findings: $WORKSPACE/findings/"
echo "3. Generate report: secbrain insights --workspace $WORKSPACE"
echo ""
