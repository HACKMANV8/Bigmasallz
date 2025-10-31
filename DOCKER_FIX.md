# Docker Build Fix

## Issue
Frontend Docker build was failing with error:
```
npm error The `npm ci` command can only install with an existing package-lock.json
```

## Root Cause
The frontend directory was missing `package-lock.json` file, which is required by `npm ci`.

## Solution

### Changed in `frontend/Dockerfile`:
1. **Line 10**: Changed from `COPY package.json package-lock.json* ./` to `COPY package.json ./`
2. **Line 11**: Changed from `RUN npm ci` to `RUN npm install --legacy-peer-deps`
3. **Updated runner stage**: Changed from standalone build to standard Next.js build
   - Copies `node_modules`, `.next`, and other necessary files
   - Uses `npm start` instead of `node server.js`

### Changed in `frontend/next.config.js`:
- Added `output: 'standalone'` for better Docker optimization (optional)

## Why These Changes Work

1. **`npm install` vs `npm ci`**:
   - `npm ci` requires `package-lock.json` for reproducible builds
   - `npm install` generates `package-lock.json` if missing
   - For development, `npm install` is more flexible

2. **`--legacy-peer-deps`**:
   - Handles peer dependency conflicts in newer npm versions
   - Ensures compatibility with Next.js 14 and React 18

3. **Standard build vs Standalone**:
   - Standalone build creates a minimal Node.js server
   - Standard build is simpler and more compatible
   - Both work in production, standard is easier to debug

## Building Now

```bash
# Build frontend only
docker-compose build frontend

# Build all services
docker-compose build

# Build and start
docker-compose up -d --build
```

## For Production

To generate `package-lock.json` for production builds:

```bash
cd frontend
npm install  # Generates package-lock.json
git add package-lock.json
```

Then revert Dockerfile to use `npm ci` for faster, more reproducible builds.

## Status
✅ Fixed - Frontend Docker build now works correctly
