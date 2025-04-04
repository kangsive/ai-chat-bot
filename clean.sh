#!/bin/bash

# Script to clean runtime files before git commit

echo "Cleaning up runtime files..."

# Clean frontend build files
if [ -d "frontend/.next" ]; then
  echo "Removing frontend build files..."
  rm -rf frontend/.next
fi

# Clean node_modules
if [ -d "frontend/node_modules" ]; then
  echo "Removing node_modules..."
  rm -rf frontend/node_modules
fi

# Clean python cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type d -name ".pytest_cache" -exec rm -rf {} +

echo "Cleanup complete. You can now safely add files to git." 