#!/bin/bash

echo "=== Threshold Network Documentation Validation ==="
echo ""

# Check all required files exist
echo "📁 Checking documentation files..."
files=(
    "README.md"
    "program.json"
    "IMMUNEFI_RESEARCH.md"
    "ATTACK_SURFACE_GUIDE.md"
    "POC_TEMPLATES.md"
    "TESTING_GUIDE.md"
    "IMPLEMENTATION_SUMMARY.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        size=$(ls -lh "$file" | awk '{print $5}')
        echo "  ✅ $file ($size)"
    else
        echo "  ❌ $file (missing)"
    fi
done

echo ""
echo "📊 Documentation Statistics:"
total_lines=$(wc -l *.md 2>/dev/null | tail -1 | awk '{print $1}')
total_size=$(du -sh . | awk '{print $1}')
echo "  - Total lines: $total_lines"
echo "  - Total size: $total_size"

echo ""
echo "🔍 Validating program.json..."
if python3 -m json.tool program.json > /dev/null 2>&1; then
    echo "  ✅ Valid JSON syntax"
    
    # Extract key metrics
    critical_contracts=$(python3 -c "import json; f=open('program.json'); data=json.load(f); print(len(data.get('critical_contracts', [])))")
    high_priority_vulns=$(python3 -c "import json; f=open('program.json'); data=json.load(f); print(len(data.get('high_priority_vulnerabilities', [])))")
    
    echo "  ✅ Critical contracts: $critical_contracts"
    echo "  ✅ High-priority vulnerabilities: $high_priority_vulns"
else
    echo "  ❌ Invalid JSON syntax"
fi

echo ""
echo "✅ Validation complete!"
