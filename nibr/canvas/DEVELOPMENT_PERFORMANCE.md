# Development Performance Guide

## Performance Optimizations Applied

### 1. Next.js Configuration Optimizations
- **SWC Minification**: Enabled for faster builds
- **Package Import Optimization**: Optimized imports for `@langchain/core` and `@langchain/langgraph`
- **Code Splitting**: Optimized chunk splitting for vendors and LangChain modules
- **Node.js Fallbacks**: Proper fallbacks for client-side builds

### 2. LangChain Fetch Configuration
- **Custom Fetch Handler**: Created `@/lib/langchain-config` to handle browser extension conflicts
- **Error Handling**: Graceful handling of fetch failures from browser extensions
- **Early Initialization**: Loaded in layout to ensure early configuration

### 3. Database Configuration
- **Local Development Path**: Using `.tmp/nibr_canvas.db` instead of `/data/` for faster access
- **Automatic Cleanup**: Database recreated on server restart to avoid lock issues

## Common Issues and Solutions

### Slow Compilation Times
**Symptoms**: Initial compilation takes 60+ seconds
**Solutions**:
1. Clear Next.js cache: `rm -rf .next`
2. Clear database: `rm -f .tmp/nibr_canvas.db*`
3. Restart development server: `npm run dev`
4. Consider using `npm run dev -- --turbo` for faster builds (experimental)

### LangChain Fetch Errors
**Symptoms**: `TypeError: Failed to fetch` with chrome-extension references
**Solutions**:
1. The custom fetch handler should prevent these errors
2. If errors persist, try disabling browser extensions temporarily
3. Check browser console for specific extension conflicts

### Authentication Issues
**Symptoms**: "There was an error signing into your account"
**Solutions**:
1. Use email format: `admin@example.com` / `admin`
2. Check server logs for specific error messages
3. Ensure database directory exists and is writable

## Development Workflow

1. **First Start**: Clear caches and restart
   ```bash
   rm -rf .next .tmp
   npm run dev
   ```

2. **Regular Development**: Just use
   ```bash
   npm run dev
   ```

3. **If Issues Arise**: Clear and restart
   ```bash
   pkill -f "npm.*dev"
   rm -f .tmp/nibr_canvas.db*
   npm run dev
   ```

## Test Accounts
Use these for development testing:
- `admin@example.com` / `admin` (Admin access)
- `researcher@example.com` / `researcher` (Standard user)
- `scientist@example.com` / `scientist` (Standard user)
- `analyst@example.com` / `analyst` (Standard user)
- `guest@example.com` / `guest` (Limited access)

## Performance Monitoring
- Initial compilation should now be under 30 seconds
- Subsequent builds should be under 5 seconds
- Authentication should be near-instant
- Database operations should be under 100ms
