#!/usr/bin/env python3
"""
Setup Data Links for Canvas
Creates symbolic links to existing biomni data to avoid duplication
"""

import os
import sys
from pathlib import Path


def create_data_links():
    """Create symbolic links to existing biomni data."""
    print("🔗 Setting up data symbolic links...")
    
    # Base paths
    canvas_backend = Path(__file__).parent / "backend"
    canvas_frontend = Path(__file__).parent / "frontend"
    biomni_root = Path(__file__).parent.parent.parent
    
    # Canvas data directory
    canvas_data_dir = canvas_backend / "data"
    canvas_data_dir.mkdir(exist_ok=True)
    
    # Links to create
    data_links = [
        {
            'source': biomni_root / "data" / "data_lake",
            'target': canvas_data_dir / "datalake",
            'description': "Biomni data lake with research datasets"
        },
        {
            'source': biomni_root / "data" / "benchmark",
            'target': canvas_data_dir / "benchmark", 
            'description': "Biomni benchmark datasets"
        },
        {
            'source': biomni_root / "data" / "cache",
            'target': canvas_data_dir / "cache",
            'description': "Biomni cache directory"
        },
        {
            'source': biomni_root / "data" / "results",
            'target': canvas_data_dir / "results",
            'description': "Biomni results directory"
        }
    ]
    
    created_links = []
    
    for link_info in data_links:
        source = link_info['source']
        target = link_info['target']
        description = link_info['description']
        
        try:
            # Remove target if it exists and is not a symlink
            if target.exists() and not target.is_symlink():
                if target.is_dir():
                    import shutil
                    shutil.rmtree(target)
                else:
                    target.unlink()
            
            # Remove existing symlink
            if target.is_symlink():
                target.unlink()
            
            # Create symlink if source exists
            if source.exists():
                target.symlink_to(source)
                print(f"  ✅ {target.name} -> {source}")
                print(f"     {description}")
                created_links.append({
                    'name': target.name,
                    'source': str(source),
                    'target': str(target),
                    'description': description
                })
            else:
                print(f"  ⚠️  {target.name} - source not found: {source}")
                
        except Exception as e:
            print(f"  ❌ Failed to create {target.name}: {e}")
    
    # Create data structure info file
    data_info = {
        'created_at': str(Path(__file__).stat().st_mtime),
        'links': created_links,
        'total_links': len(created_links),
        'description': 'Symbolic links to existing biomni data to avoid duplication'
    }
    
    info_file = canvas_data_dir / "data_links.json"
    import json
    with open(info_file, 'w') as f:
        json.dump(data_info, f, indent=2)
    
    print(f"\n✅ Created {len(created_links)} data links")
    print(f"📄 Link information saved to: {info_file}")
    
    return len(created_links) > 0


def check_data_availability():
    """Check what data is available through the links."""
    print("\n🔍 Checking data availability...")
    
    canvas_data_dir = Path(__file__).parent / "backend" / "data"
    
    # Check each expected data directory
    data_dirs = ['datalake', 'benchmark', 'cache', 'results']
    
    available_data = {}
    
    for data_dir in data_dirs:
        dir_path = canvas_data_dir / data_dir
        
        if dir_path.exists():
            if dir_path.is_symlink():
                source = dir_path.readlink()
                print(f"  ✅ {data_dir} -> {source}")
                
                # Count files in directory
                try:
                    file_count = sum(1 for _ in dir_path.rglob('*') if _.is_file())
                    dir_count = sum(1 for _ in dir_path.rglob('*') if _.is_dir())
                    available_data[data_dir] = {
                        'files': file_count,
                        'directories': dir_count,
                        'source': str(source)
                    }
                    print(f"     Files: {file_count}, Directories: {dir_count}")
                except Exception as e:
                    print(f"     Error counting: {e}")
                    available_data[data_dir] = {'error': str(e)}
            else:
                print(f"  📁 {data_dir} (regular directory)")
        else:
            print(f"  ❌ {data_dir} not found")
    
    return available_data


def main():
    """Main function to setup data links."""
    print("🎯 Canvas Data Links Setup")
    print("=" * 40)
    
    try:
        # Create symbolic links
        success = create_data_links()
        
        if success:
            # Check data availability
            available_data = check_data_availability()
            
            print("\n📊 Data Summary:")
            total_files = sum(data.get('files', 0) for data in available_data.values() if isinstance(data, dict))
            total_dirs = sum(data.get('directories', 0) for data in available_data.values() if isinstance(data, dict))
            
            print(f"  Total files accessible: {total_files}")
            print(f"  Total directories: {total_dirs}")
            print(f"  Data links created: {len(available_data)}")
            
            print("\n🎉 Data links setup complete!")
            print("Canvas now has access to existing biomni data without duplication.")
            
        else:
            print("\n⚠️  No data links created.")
            print("Check that biomni data directories exist.")
            
        return success
        
    except Exception as e:
        print(f"\n❌ Data links setup failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
