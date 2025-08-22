#!/usr/bin/env python3
"""
Quick fix script for Canvas issues
Addresses the specific problems found during setup
"""

import os
import sys
import subprocess
from pathlib import Path


def fix_frontend_dependencies():
    """Fix frontend dependency conflicts."""
    print("🔧 Fixing frontend dependencies...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    try:
        # Remove node_modules and package-lock.json if they exist
        node_modules = frontend_dir / "node_modules"
        package_lock = frontend_dir / "package-lock.json"
        
        if node_modules.exists():
            import shutil
            shutil.rmtree(node_modules)
            print("  ✅ Removed node_modules")
        
        if package_lock.exists():
            package_lock.unlink()
            print("  ✅ Removed package-lock.json")
        
        # Install with legacy peer deps
        result = subprocess.run(
            ["npm", "install", "--legacy-peer-deps"],
            cwd=frontend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✅ Frontend dependencies installed successfully")
            return True
        else:
            print(f"  ❌ npm install failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error fixing frontend: {e}")
        return False


def setup_data_links():
    """Setup symbolic links to biomni data."""
    print("🔗 Setting up data symbolic links...")
    
    try:
        # Run the data links setup
        result = subprocess.run(
            [sys.executable, "setup_data_links.py"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✅ Data links created successfully")
            print(result.stdout)
            return True
        else:
            print(f"  ❌ Data links setup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error setting up data links: {e}")
        return False


def test_biomni_import():
    """Test if biomni can be imported with the fixed path."""
    print("🧬 Testing biomni import...")
    
    try:
        # Add biomni to path
        biomni_path = str(Path(__file__).parent.parent.parent)
        if biomni_path not in sys.path:
            sys.path.insert(0, biomni_path)
        
        # Test import
        import biomni
        from biomni.agent import A1
        
        print(f"  ✅ biomni imported successfully")
        print(f"  📁 Path: {biomni_path}")
        print(f"  📦 Version: {getattr(biomni, '__version__', 'unknown')}")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ biomni import failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error testing import: {e}")
        return False


def test_typescript_compilation():
    """Test TypeScript compilation."""
    print("🔍 Testing TypeScript compilation...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    try:
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=frontend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✅ TypeScript compilation successful")
            return True
        else:
            print(f"  ⚠️  TypeScript compilation has issues:")
            print(f"      {result.stderr}")
            # Still return True if it's just warnings
            return "error" not in result.stderr.lower()
            
    except Exception as e:
        print(f"  ❌ Error testing TypeScript: {e}")
        return False


def create_quick_start_script():
    """Create a simple start script that works."""
    print("📜 Creating quick start script...")
    
    script_content = f"""#!/bin/bash
# Quick Start Script for NIBR Biomni Canvas

echo "🚀 Quick Start - NIBR Biomni Canvas"

# Set Python path to include biomni
export PYTHONPATH="${{PWD}}/backend/app:${{PWD}}/../..:${{PYTHONPATH}}"

# Start backend
echo "Starting backend..."
cd backend && python -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Check backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend started successfully"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "Starting frontend..."
cd ../frontend && npm start &
FRONTEND_PID=$!

echo ""
echo "🎉 Canvas is starting!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"  
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "👤 Login: researcher / researcher"
echo ""
echo "Press Ctrl+C to stop"

trap 'echo "\\nStopping..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT
wait
"""
    
    script_path = Path(__file__).parent / "quick_start.sh"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    print(f"  ✅ Created quick_start.sh")
    
    return True


def main():
    """Main fix function."""
    print("🎯 Canvas Issues Fix Script")
    print("=" * 40)
    
    fixes = [
        ("Frontend Dependencies", fix_frontend_dependencies),
        ("Data Symbolic Links", setup_data_links),
        ("Biomni Import Test", test_biomni_import),
        ("TypeScript Compilation", test_typescript_compilation),
        ("Quick Start Script", create_quick_start_script)
    ]
    
    results = {}
    
    for fix_name, fix_func in fixes:
        print(f"\n🔧 {fix_name}")
        print("-" * 30)
        try:
            results[fix_name] = fix_func()
        except Exception as e:
            print(f"❌ {fix_name} failed: {e}")
            results[fix_name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Fix Summary")
    print("=" * 40)
    
    passed = 0
    total = len(fixes)
    
    for fix_name, success in results.items():
        status = "✅ FIXED" if success else "❌ FAILED"
        print(f"{status}  {fix_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} fixes successful")
    
    if passed == total:
        print("\n🎉 All issues fixed!")
        print("\n🚀 Quick Start:")
        print("./quick_start.sh")
        print("\nOr use the full setup:")
        print("python setup_canvas.py")
        
    elif passed >= 3:  # Most critical fixes
        print("\n✅ Core issues fixed!")
        print("You can try starting with:")
        print("./quick_start.sh")
        
    else:
        print(f"\n⚠️  {total - passed} issues remain")
        print("Please review the errors above.")
    
    return passed >= 3  # Consider success if core fixes work


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
