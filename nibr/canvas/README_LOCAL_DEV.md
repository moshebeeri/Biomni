# NIBR Biomni Canvas - Local Development Guide

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.9+
- Yarn package manager
- Git

### Setup Instructions

1. **Navigate to the canvas directory:**
```bash
cd /Users/mb/projects/novartis/biomni/nibr/canvas
```

2. **Run the setup script:**
```bash
./setup-dev.sh
```

This script will:
- Check prerequisites
- Create local data directories in `/tmp/nibr_data`
- Set up environment variables
- Install all dependencies
- Install biomni Python package
- Create startup scripts

3. **Configure API Keys:**

Edit `.env.local` and add your API keys:
```bash
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
```

4. **Start the development server:**
```bash
./start-dev.sh
```

This will start:
- LangGraph server on http://localhost:54367
- Next.js dev server on http://localhost:3000

## 🔐 Login Credentials

For local development:
- **Username:** admin
- **Password:** admin

## 📁 Project Structure

```
nibr/canvas/
├── apps/
│   ├── agents/          # LangGraph agents + Biomni integration
│   │   └── src/biomni/  # Biomni agent wrapper
│   └── web/             # Next.js frontend
│       └── src/
│           ├── app/api/ # API routes
│           └── lib/     # Auth & storage implementations
├── scripts/
│   └── biomni_wrapper.py # Python bridge for Biomni
├── .env.local           # Local environment variables
├── setup-dev.sh         # Setup script
└── start-dev.sh         # Startup script
```

## 🧪 Testing the Integration

### 1. Test API Endpoint
```bash
curl http://localhost:3000/api/biomni/test
```

Expected response:
```json
{
  "status": "ok",
  "message": "NIBR Biomni Canvas API is running",
  "authenticated": false,
  "environment": {
    "node_version": "v18.x.x",
    "env": "development",
    "nibr_env": "local-dev"
  }
}
```

### 2. Test Authentication
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

### 3. Test Biomni Agent (Python)
```python
# Test biomni installation
python3 -c "from biomni.agent import A1; print('Biomni installed successfully')"
```

## 🔧 Troubleshooting

### Issue: Module not found errors
**Solution:** Install dependencies
```bash
yarn install
pip3 install biomni better-sqlite3 python-dotenv
```

### Issue: Permission denied on scripts
**Solution:** Make scripts executable
```bash
chmod +x setup-dev.sh start-dev.sh
chmod +x scripts/biomni_wrapper.py
```

### Issue: Port already in use
**Solution:** Kill existing processes
```bash
# Find processes on ports
lsof -i :3000
lsof -i :54367

# Kill processes
kill -9 <PID>
```

### Issue: SQLite database errors
**Solution:** Reset the database
```bash
rm -rf /tmp/nibr_data/db
mkdir -p /tmp/nibr_data/db
```

### Issue: Python/Biomni not found
**Solution:** Check Python path
```bash
which python3
python3 --version
pip3 list | grep biomni
```

## 📊 Local Data Storage

All data is stored in `/tmp/nibr_data/`:
- `/tmp/nibr_data/agents/` - Agent states and data
- `/tmp/nibr_data/uploads/` - Uploaded files
- `/tmp/nibr_data/db/` - SQLite database
- `/tmp/nibr_data/datalake/` - Data lake files

**Note:** `/tmp` is cleared on Mac restart. For persistent storage, change `DATA_DIR` in `setup-dev.sh` to a permanent location.

## 🔄 Development Workflow

1. **Make code changes**
2. **The dev server auto-reloads** (Next.js hot reload)
3. **For agent changes**, restart the LangGraph server:
   ```bash
   # In apps/agents directory
   yarn dev
   ```

## 🐛 Debug Mode

To see detailed logs:

1. **Enable debug logging in `.env.local`:**
```bash
NIBR_ENABLE_LOGGING=true
DEBUG=biomni:*
```

2. **Check Python wrapper logs:**
```bash
# The Python wrapper outputs to stdout
# Check the terminal where start-dev.sh is running
```

3. **Check Next.js logs:**
```bash
# Development server logs appear in the terminal
```

## 🚢 Next Steps

After confirming local development works:

1. **Test Biomni Integration:**
   - Create a research task
   - Add custom tools
   - Upload data files

2. **Customize for NIBR:**
   - Modify UI components
   - Add NIBR-specific tools
   - Configure AD authentication

3. **Deploy to Container:**
   - Build Docker image
   - Deploy to NIBR infrastructure

## 📝 Notes

- This is a development setup with mock AD authentication
- Data is stored locally in `/tmp` (non-persistent on Mac)
- The biomni Python package must be installed separately
- API keys are required for LLM functionality

## 🆘 Support

For issues specific to:
- **Open Canvas**: Check the original repo issues
- **Biomni**: Refer to biomni documentation
- **NIBR Integration**: Contact the NIBR team

---

**Version:** 1.0.0  
**Last Updated:** 2024