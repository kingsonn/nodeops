#!/bin/bash

echo "========================================"
echo "Cleaning MetaMask SDK Dependencies"
echo "========================================"

echo ""
echo "Step 1: Removing node_modules..."
rm -rf node_modules

echo ""
echo "Step 2: Removing package-lock.json..."
rm -f package-lock.json

echo ""
echo "Step 3: Removing .next build cache..."
rm -rf .next

echo ""
echo "Step 4: Installing clean dependencies..."
npm install

echo ""
echo "Step 5: Verifying no @metamask/sdk..."
if npm list @metamask/sdk 2>/dev/null; then
    echo "WARNING: @metamask/sdk still found!"
else
    echo "SUCCESS: No @metamask/sdk found"
fi

echo ""
echo "========================================"
echo "Cleanup Complete!"
echo "========================================"
echo ""
echo "Now run: npm run dev"
echo ""
