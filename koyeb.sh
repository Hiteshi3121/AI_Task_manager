#!/bin/bash
# Koyeb build script — builds frontend then installs backend deps
set -e

echo "=== Installing frontend dependencies and building ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Copying frontend dist to backend ==="
rm -rf backend/frontend_dist
cp -r frontend/dist backend/frontend_dist

echo "=== Installing backend dependencies ==="
cd backend
pip install -r requirements.txt

echo "=== Build complete ==="
