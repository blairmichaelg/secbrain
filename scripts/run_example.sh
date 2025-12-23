#!/bin/bash
# Example script for running SecBrain with proper RPC configuration
# 
# This script demonstrates best practices for configuring RPC URLs
# to avoid common pitfalls.

set -e  # Exit on error

# =============================================================================
# CONFIGURATION
# =============================================================================

# Target configuration
SCOPE_FILE="./secbrain/examples/originprotocol/scope.yaml"
PROGRAM_FILE="./secbrain/examples/originprotocol/program.json"
WORKSPACE_DIR="./targets/originprotocol"

# RPC Configuration
# IMPORTANT: Always use quotes around URLs to prevent shell interpretation
RPC_URL="https://ethereum.publicnode.com"

# Alternative: Use Alchemy (requires API key)
# RPC_URL="https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}"

# Alternative: Use Infura (requires API key)
# RPC_URL="https://mainnet.infura.io/v3/${INFURA_API_KEY}"

# Block number (optional - pins to specific block for reproducibility)
BLOCK_NUMBER=""  # Leave empty for latest block
# BLOCK_NUMBER="18500000"  # Uncomment to pin to specific block

# =============================================================================
# VALIDATION
# =============================================================================

echo "🔍 Validating configuration..."

# Check if scope file exists
if [ ! -f "$SCOPE_FILE" ]; then
    echo "❌ Error: Scope file not found: $SCOPE_FILE"
    exit 1
fi

# Check if program file exists
if [ ! -f "$PROGRAM_FILE" ]; then
    echo "❌ Error: Program file not found: $PROGRAM_FILE"
    exit 1
fi

# Check if required API keys are set
if [ -z "$TOGETHER_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: No API keys found for model providers."
    echo "   Set TOGETHER_API_KEY or OPENAI_API_KEY environment variable."
    echo "   Continuing with dry-run mode..."
fi

# =============================================================================
# EXECUTION
# =============================================================================

echo "🚀 Starting SecBrain run..."
echo "   Scope: $SCOPE_FILE"
echo "   Program: $PROGRAM_FILE"
echo "   Workspace: $WORKSPACE_DIR"
echo "   RPC URL: $RPC_URL"
if [ -n "$BLOCK_NUMBER" ]; then
    echo "   Block: $BLOCK_NUMBER"
fi
echo ""

# Create workspace directory
mkdir -p "$WORKSPACE_DIR"

# Build command arguments
CMD_ARGS=(
    "run"
    "--scope" "$SCOPE_FILE"
    "--program" "$PROGRAM_FILE"
    "--workspace" "$WORKSPACE_DIR"
    "--no-dry-run"
)

# Add RPC URL if specified
if [ -n "$RPC_URL" ]; then
    CMD_ARGS+=("--rpc-url" "$RPC_URL")
fi

# Add block number if specified
if [ -n "$BLOCK_NUMBER" ]; then
    CMD_ARGS+=("--block-number" "$BLOCK_NUMBER")
fi

# Execute SecBrain
# Note: Using array expansion ensures proper quoting
secbrain "${CMD_ARGS[@]}"

# =============================================================================
# POST-EXECUTION
# =============================================================================

echo ""
echo "✅ SecBrain run completed!"
echo "📁 Results are in: $WORKSPACE_DIR"
echo ""
echo "Next steps:"
echo "  1. Review findings: ls $WORKSPACE_DIR/findings/"
echo "  2. Check logs: tail $WORKSPACE_DIR/logs/*.jsonl"
echo "  3. Generate insights: secbrain insights --workspace $WORKSPACE_DIR"
