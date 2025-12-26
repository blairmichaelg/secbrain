#!/bin/bash
# Setup script for Kiln Staking Contracts vulnerability research
# This script automates the environment setup described in the hunting guide

set -e  # Exit on error

echo "=================================================="
echo "Kiln Staking Contracts - Vulnerability Hunt Setup"
echo "=================================================="
echo ""

# Configuration
TARGET_REPO="https://github.com/kilnfi/staking-contracts"
TARGET_COMMIT="f33eb8dc37fab40217dbe1e69853ca3fcd884a2d"
WORKSPACE_DIR="${WORKSPACE_DIR:-./workspace}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "1. Checking prerequisites..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ git is installed${NC}"

# Check if foundry is installed
if ! command -v forge &> /dev/null; then
    echo -e "${YELLOW}Warning: Foundry is not installed${NC}"
    echo "Installing Foundry..."
    curl -L https://foundry.paradigm.xyz | bash
    source ~/.bashrc
    foundryup
fi
echo -e "${GREEN}✓ Foundry is installed${NC}"

# Check for Alchemy API key
if [ -z "$MAINNET_RPC_URL" ]; then
    echo -e "${YELLOW}Warning: MAINNET_RPC_URL is not set${NC}"
    echo "Please set it with:"
    echo "  export MAINNET_RPC_URL='https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY'"
    echo ""
    read -p "Do you want to set it now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your Alchemy API URL: " ALCHEMY_URL
        export MAINNET_RPC_URL="$ALCHEMY_URL"
        echo "export MAINNET_RPC_URL='$ALCHEMY_URL'" >> ~/.bashrc
        echo -e "${GREEN}✓ MAINNET_RPC_URL set${NC}"
    else
        echo -e "${RED}You'll need to set MAINNET_RPC_URL before running tests${NC}"
    fi
else
    echo -e "${GREEN}✓ MAINNET_RPC_URL is set${NC}"
fi

echo ""
echo "2. Setting up workspace..."

# Create workspace directory
mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"

# Clone target repository
if [ -d "staking-contracts" ]; then
    echo -e "${YELLOW}Target repository already exists, skipping clone${NC}"
    cd staking-contracts
    git fetch
else
    echo "Cloning target repository..."
    git clone "$TARGET_REPO"
    cd staking-contracts
fi

# Checkout specific commit
echo "Checking out target commit: $TARGET_COMMIT"
git checkout "$TARGET_COMMIT"
echo -e "${GREEN}✓ Repository ready${NC}"

echo ""
echo "3. Installing dependencies..."

# Install foundry dependencies
if [ -f "foundry.toml" ]; then
    forge install --no-commit
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${YELLOW}No foundry.toml found, skipping dependency installation${NC}"
fi

# Copy our custom foundry.toml if it doesn't exist
if [ ! -f "foundry.toml" ]; then
    echo "Copying foundry.toml from templates..."
    cp ../../targets/kiln-staking/foundry.toml .
    echo -e "${GREEN}✓ foundry.toml configured${NC}"
fi

# Create test directory if it doesn't exist
mkdir -p test

echo ""
echo "4. Copying PoC templates..."

# Copy test templates
cp ../../targets/kiln-staking/test/FeeExtractionDoS.t.sol test/ 2>/dev/null || echo -e "${YELLOW}FeeExtractionDoS.t.sol already exists${NC}"
cp ../../targets/kiln-staking/test/RoundingErrorDoS.t.sol test/ 2>/dev/null || echo -e "${YELLOW}RoundingErrorDoS.t.sol already exists${NC}"
cp ../../targets/kiln-staking/test/InitializableVulnerability.t.sol test/ 2>/dev/null || echo -e "${YELLOW}InitializableVulnerability.t.sol already exists${NC}"

echo -e "${GREEN}✓ PoC templates ready${NC}"

echo ""
echo "5. Testing the setup..."

# Test forge compilation
if forge build --force > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Forge build successful${NC}"
else
    echo -e "${YELLOW}Warning: Forge build had errors (this is normal if dependencies are missing)${NC}"
fi

# Test fork connection (if RPC URL is set)
if [ -n "$MAINNET_RPC_URL" ]; then
    echo "Testing mainnet fork connection..."
    if forge test --fork-url "$MAINNET_RPC_URL" --list > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Fork connection successful${NC}"
    else
        echo -e "${YELLOW}Warning: Could not connect to mainnet fork${NC}"
    fi
fi

echo ""
echo "=================================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Review the hunting guide: cat ../../targets/kiln-staking/README.md"
echo "2. Examine the target contracts in src/"
echo "3. Customize the PoC templates in test/"
echo "4. Run tests with: forge test --fork-url \$MAINNET_RPC_URL -vvvv"
echo ""
echo "Quick commands:"
echo "  forge test --fork-url \$MAINNET_RPC_URL --match-test testFeeRecipientDoS -vvvv"
echo "  forge test --fork-url \$MAINNET_RPC_URL --match-test testOneWeiInflationAttack -vvvv"
echo "  forge test --fork-url \$MAINNET_RPC_URL --match-test testProxyReinitialization -vvvv"
echo ""
echo "Documentation:"
echo "  README: ../../targets/kiln-staking/README.md"
echo "  Report Template: ../../targets/kiln-staking/REPORT_TEMPLATE.md"
echo "  Submission Guide: ../../targets/kiln-staking/SUBMISSION_STRATEGY.md"
echo ""
echo -e "${YELLOW}Remember to check previous audits before submitting!${NC}"
echo ""
