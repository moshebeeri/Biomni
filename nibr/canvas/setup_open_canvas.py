#!/usr/bin/env python3
"""
Proper NIBR Biomni Canvas Integration Setup
Works with the existing NIBR Biomni Canvas structure
"""

import os
import sys
import subprocess
from pathlib import Path


def setup_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        # Python dependencies for biomni integration
        python_deps = [
            "python-shell",  # For Node.js <-> Python communication
            "dill",          # For persistent agent serialization
            "cloudpickle"    # Alternative serialization
        ]
        
        for dep in python_deps:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"  ✅ {dep}")
        
        # Node.js dependencies
        print("  Installing Node.js dependencies...")
        subprocess.run(["npm", "install", "--legacy-peer-deps", "--ignore-scripts"], cwd="apps/web", check=True)
        subprocess.run(["npm", "install", "--legacy-peer-deps", "--ignore-scripts"], cwd="apps/agents", check=True)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to install dependencies: {e}")
        return False


def setup_data_links():
    """Setup symbolic links to biomni data."""
    print("🔗 Setting up data links...")
    
    try:
        # Create data directory in apps/web for data access
        data_dir = Path("apps/web/data")
        data_dir.mkdir(exist_ok=True)
        
        # Links to existing biomni data
        biomni_data = Path("../../data")
        
        links = [
            ("datalake", biomni_data / "data_lake"),
            ("benchmark", biomni_data / "benchmark"),
            ("cache", biomni_data / "cache")
        ]
        
        for link_name, source in links:
            target = data_dir / link_name
            
            if target.exists() and target.is_symlink():
                target.unlink()
            elif target.exists():
                import shutil
                shutil.rmtree(target)
            
            if source.exists():
                target.symlink_to(source)
                print(f"  ✅ {link_name} -> {source}")
            else:
                print(f"  ⚠️  {link_name} - source not found")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to setup data links: {e}")
        return False


def test_integration():
    """Test the integration."""
    print("🧪 Testing integration...")
    
    try:
        # Test biomni import
        sys.path.insert(0, str(Path.cwd().parent.parent))
        import biomni
        print("  ✅ Biomni import successful")
        
        # Test Node.js structure (skip build for now)
        package_json = Path("apps/web/package.json")
        if package_json.exists():
            print("  ✅ Next.js project structure valid")
        else:
            print("  ⚠️  Next.js project structure missing")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Testing failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🎯 NIBR Biomni Canvas Integration Setup")
    print("=" * 50)
    
    steps = [
        ("Dependencies", setup_dependencies),
        ("Data Links", setup_data_links),
        ("Integration Test", test_integration)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔧 {step_name}")
        print("-" * 30)
        success = step_func()
        if not success:
            print(f"❌ {step_name} failed")
            return False
    
    print("\n🎉 Setup complete!")
    print("\n🚀 Next steps:")
    print("1. Start development: npm run dev (in apps/web)")
    print("2. Test biomni API: GET http://localhost:3000/api/biomni/test")
    print("3. Execute research: POST http://localhost:3000/api/biomni/test")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
