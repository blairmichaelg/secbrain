#!/bin/bash
# Run bounty hunting workflows for Threshold Network
# This script provides easy access to trigger the bounty hunting workflows

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SecBrain Bounty Workflow Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

echo -e "${GREEN}✓ GitHub CLI is installed and authenticated${NC}"
echo ""

# Menu
echo "Select a bounty hunting workflow to run:"
echo ""
echo "  1) Threshold Network Bounty Hunt (Full SecBrain Analysis)"
echo "  2) Foundry Bounty Hunt (Intensive Testing & Fuzzing)"
echo "  3) SecBrain Auto PR (Create PR with Results)"
echo "  4) View Workflow Status"
echo "  5) Exit"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo -e "${YELLOW}Threshold Network Bounty Hunt${NC}"
        echo ""
        echo "Run mode:"
        echo "  1) Dry-run (no API costs, validation only)"
        echo "  2) Full analysis (uses API credits)"
        read -p "Select mode (1-2): " mode_choice
        
        echo ""
        echo "Scope type:"
        echo "  1) Full (all contracts)"
        echo "  2) Critical (high-value contracts only)"
        read -p "Select scope (1-2): " scope_choice
        
        RUN_MODE="dry-run"
        if [ "$mode_choice" = "2" ]; then
            RUN_MODE="full"
        fi
        
        SCOPE_TYPE="full"
        if [ "$scope_choice" = "2" ]; then
            SCOPE_TYPE="critical"
        fi
        
        echo ""
        echo -e "${YELLOW}Starting Threshold Network Bounty Hunt...${NC}"
        echo "  Mode: $RUN_MODE"
        echo "  Scope: $SCOPE_TYPE"
        echo ""
        
        gh workflow run threshold-bounty-hunt.yml \
            -f run_mode="$RUN_MODE" \
            -f scope_type="$SCOPE_TYPE"
        
        echo ""
        echo -e "${GREEN}✓ Workflow triggered successfully!${NC}"
        echo ""
        echo "View progress: gh run watch"
        echo "Or visit: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions"
        ;;
    
    2)
        echo ""
        echo -e "${YELLOW}Foundry Bounty Hunt${NC}"
        echo ""
        read -p "Target (default: thresholdnetwork): " target_input
        TARGET="${target_input:-thresholdnetwork}"
        
        read -p "Fuzz runs (default: 50000): " fuzz_input
        FUZZ_RUNS="${fuzz_input:-50000}"
        
        read -p "Invariant runs (default: 5000): " inv_input
        INV_RUNS="${inv_input:-5000}"
        
        echo ""
        echo -e "${YELLOW}Starting Foundry Bounty Hunt...${NC}"
        echo "  Target: $TARGET"
        echo "  Fuzz runs: $FUZZ_RUNS"
        echo "  Invariant runs: $INV_RUNS"
        echo ""
        
        gh workflow run foundry-bounty-hunt.yml \
            -f target="$TARGET" \
            -f fuzz_runs="$FUZZ_RUNS" \
            -f invariant_runs="$INV_RUNS"
        
        echo ""
        echo -e "${GREEN}✓ Workflow triggered successfully!${NC}"
        echo ""
        echo "This may take 1-3 hours depending on configuration."
        echo "View progress: gh run watch"
        ;;
    
    3)
        echo ""
        echo -e "${YELLOW}SecBrain Auto PR${NC}"
        echo ""
        echo "Target:"
        echo "  1) thresholdnetwork"
        echo "  2) originprotocol"
        read -p "Select target (1-2): " target_choice
        
        TARGET="thresholdnetwork"
        if [ "$target_choice" = "2" ]; then
            TARGET="originprotocol"
        fi
        
        echo ""
        echo "Run mode:"
        echo "  1) Dry-run"
        echo "  2) Full"
        read -p "Select mode (1-2): " mode_choice
        
        RUN_MODE="dry-run"
        if [ "$mode_choice" = "2" ]; then
            RUN_MODE="full"
        fi
        
        echo ""
        read -p "Branch name (press Enter for auto-generated): " BRANCH_NAME
        
        echo ""
        echo -e "${YELLOW}Starting SecBrain Auto PR...${NC}"
        echo "  Target: $TARGET"
        echo "  Mode: $RUN_MODE"
        if [ -n "$BRANCH_NAME" ]; then
            echo "  Branch: $BRANCH_NAME"
        fi
        echo ""
        
        if [ -n "$BRANCH_NAME" ]; then
            gh workflow run secbrain-auto-pr.yml \
                -f target="$TARGET" \
                -f run_mode="$RUN_MODE" \
                -f branch_name="$BRANCH_NAME"
        else
            gh workflow run secbrain-auto-pr.yml \
                -f target="$TARGET" \
                -f run_mode="$RUN_MODE"
        fi
        
        echo ""
        echo -e "${GREEN}✓ Workflow triggered successfully!${NC}"
        echo ""
        echo "A PR will be created with the results."
        echo "View progress: gh run watch"
        ;;
    
    4)
        echo ""
        echo -e "${YELLOW}Recent Workflow Runs:${NC}"
        echo ""
        gh run list --limit 10
        echo ""
        echo "View details: gh run view <run-id>"
        echo "Watch live: gh run watch"
        ;;
    
    5)
        echo ""
        echo "Exiting..."
        exit 0
        ;;
    
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Useful Commands:${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "  View all runs:        gh run list"
echo "  Watch current run:    gh run watch"
echo "  View run details:     gh run view <run-id>"
echo "  Download artifacts:   gh run download <run-id>"
echo "  View workflow files:  ls -la .github/workflows/"
echo ""
echo "For more information, see: .github/workflows/BOUNTY_WORKFLOWS_README.md"
echo ""
