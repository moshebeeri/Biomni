#!/usr/bin/env python3
"""
Test script to verify NIBR Biomni Canvas integration
"""

import requests
import json
import sys
import os
from pathlib import Path


def test_server_running():
    """Test if the development server is running."""
    print("🌐 Testing development server...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        print(f"  ✅ Server responding with status {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("  ❌ Server not responding")
        return False
    except Exception as e:
        print(f"  ❌ Server test failed: {e}")
        return False


def test_biomni_api():
    """Test the biomni API endpoint."""
    print("🧬 Testing biomni API endpoint...")
    
    try:
        # Test GET endpoint
        response = requests.get("http://localhost:3000/api/biomni/test", timeout=10)
        print(f"  📡 GET /api/biomni/test: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ API responding: {data.get('message', 'Unknown response')}")
            return True
        else:
            print(f"  ❌ API returned {response.status_code}: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"  ❌ API test failed: {e}")
        return False


def test_biomni_execution():
    """Test biomni execution through API."""
    print("🔬 Testing biomni execution...")
    
    try:
        # Test POST endpoint with a simple prompt
        payload = {
            "prompt": "Hello, this is a test of the biomni integration.",
            "action": "execute"
        }
        
        response = requests.post(
            "http://localhost:3000/api/biomni/test",
            json=payload,
            timeout=30
        )
        
        print(f"  📡 POST /api/biomni/test: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Execution successful: {data.get('status', 'Unknown')}")
            if 'result' in data:
                print(f"  📄 Result preview: {str(data['result'])[:100]}...")
            return True
        else:
            print(f"  ❌ Execution failed {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Execution test failed: {e}")
        return False


def test_biomni_import():
    """Test direct biomni import."""
    print("🐍 Testing direct biomni import...")
    
    try:
        # Add biomni to path
        biomni_path = str(Path(__file__).parent.parent.parent)
        if biomni_path not in sys.path:
            sys.path.insert(0, biomni_path)
        
        import biomni
        from biomni.agent import A1
        
        print(f"  ✅ Biomni imported successfully")
        print(f"  📦 Version: {getattr(biomni, '__version__', 'unknown')}")
        
        # Test agent creation
        test_agent = A1(path="/tmp/test_agent")
        print(f"  ✅ A1 agent created successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Biomni import failed: {e}")
        return False


def test_data_links():
    """Test that data symlinks are working."""
    print("🔗 Testing data symbolic links...")
    
    data_dir = Path(__file__).parent / "apps" / "web" / "data"
    
    links_to_check = ["datalake", "benchmark", "cache"]
    working_links = 0
    
    for link_name in links_to_check:
        link_path = data_dir / link_name
        
        if link_path.exists() and link_path.is_symlink():
            target = link_path.readlink()
            print(f"  ✅ {link_name} -> {target}")
            working_links += 1
        else:
            print(f"  ❌ {link_name} link not found")
    
    if working_links == len(links_to_check):
        print(f"  ✅ All {working_links} data links working")
        return True
    else:
        print(f"  ⚠️  Only {working_links}/{len(links_to_check)} links working")
        return working_links > 0


def test_persistent_agent():
    """Test persistent agent functionality."""
    print("💾 Testing persistent agent...")
    
    try:
        # Check if persistent agent file exists
        persistent_agent_path = Path(__file__).parent / "scripts" / "persistent_agent.py"
        
        if persistent_agent_path.exists():
            print(f"  ✅ Persistent agent script found")
            
            # Try to import (add path first)
            scripts_path = str(persistent_agent_path.parent)
            if scripts_path not in sys.path:
                sys.path.insert(0, scripts_path)
            
            # Add biomni path
            biomni_path = str(Path(__file__).parent.parent.parent)
            if biomni_path not in sys.path:
                sys.path.insert(0, biomni_path)
            
            try:
                from persistent_agent import GlobalAgentManager, PersistentA1
                print(f"  ✅ Persistent agent classes imported")
                
                # Test manager creation
                manager = GlobalAgentManager(base_path="/tmp/test_persistent")
                print(f"  ✅ GlobalAgentManager created")
                
                return True
                
            except ImportError as e:
                print(f"  ⚠️  Persistent agent import failed: {e}")
                return False
                
        else:
            print(f"  ❌ Persistent agent script not found at {persistent_agent_path}")
            return False
            
    except Exception as e:
        print(f"  ❌ Persistent agent test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🎯 NIBR Biomni Canvas + Biomni Integration Test")
    print("=" * 50)
    
    tests = [
        ("Server Running", test_server_running),
        ("Biomni Import", test_biomni_import),
        ("Data Links", test_data_links),
        ("Persistent Agent", test_persistent_agent),
        ("Biomni API", test_biomni_api),
        ("Biomni Execution", test_biomni_execution),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Integration Test Summary")
    print("=" * 50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print("🚀 NIBR Biomni Canvas integration is working!")
        print("\n📱 Access the Canvas at: http://localhost:3000")
        print("🧪 API endpoint: http://localhost:3000/api/biomni/test")
        
    elif passed >= 4:  # Core functionality working
        print("\n✅ Core integration working!")
        print("🚀 NIBR Biomni Canvas basic functionality ready!")
        
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("Please review the errors above.")
    
    return passed >= 4


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
