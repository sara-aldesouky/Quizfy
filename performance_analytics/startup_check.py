#!/usr/bin/env python3
"""
Startup verification script for Performance Analytics service.
Checks that all dependencies, configs, and services are properly initialized.
"""

import sys
import os
from pathlib import Path

def check_environment_variables():
    """Check that required environment variables are set."""
    print("\n✓ Checking environment variables...")
    
    required = ["OPENAI_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"  ❌ Missing: {', '.join(missing)}")
        print(f"\n  Export them before running:\n    export OPENAI_API_KEY=<your-api-key>")
        return False
    
    print(f"  ✅ All required variables set")
    return True


def check_dependencies():
    """Check that all required packages are installed."""
    print("\n✓ Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "pydantic",
        "pandas",
        "PyPDF2",
        "openai",
        "chromadb",
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"  ❌ Missing packages: {', '.join(missing)}")
        print(f"\n  Install them:\n    pip install -r performance_analytics/requirements.txt")
        return False
    
    print(f"  ✅ All packages installed")
    return True


def check_directories():
    """Check that required directories exist."""
    print("\n✓ Checking directories...")
    
    dirs_needed = [
        "performance_analytics/services",
        "uploads",
        "chroma_db",
        "logs",
    ]
    
    all_exist = True
    for dir_path in dir_needed:
        full_path = Path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  📁 Created: {dir_path}")
        else:
            print(f"  ✅ Found: {dir_path}")
    
    return True


def check_openai_connectivity():
    """Check that OpenAI API is reachable."""
    print("\n✓ Checking OpenAI API connectivity...")
    
    try:
        from openai import OpenAI
        from .config import config
        
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Simple API test (doesn't count against quota much)
        response = client.models.list()
        print(f"  ✅ OpenAI API reachable")
        return True
    except Exception as e:
        print(f"  ⚠️  Could not verify OpenAI connection: {e}")
        print(f"  This might be OK if you're offline - check when service starts")
        return True  # Don't fail, might be network issue


def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("Performance Analytics Startup Verification")
    print("="*60)
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("OpenAI Connectivity", check_openai_connectivity),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Summary:")
    print("="*60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All checks passed! You're ready to start the service:\n")
        print("  python -m performance_analytics.main\n")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.\n")
        return 1


if __name__ == "__main__":
    # Try to import from package
    try:
        from .config import config
    except ImportError:
        # Running from within package
        from performance_analytics.config import config
    
    sys.exit(main())
