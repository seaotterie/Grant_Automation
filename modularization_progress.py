#!/usr/bin/env python3
"""
Modularization Progress Tracker
Demonstrates the current state of modularization from monolithic main.py
"""

from pathlib import Path
import sys
import re

# Add src to path
sys.path.append(str(Path(__file__).parent))

def count_lines_in_file(file_path):
    """Count lines in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception:
        return 0

def count_routes_in_file(file_path):
    """Count FastAPI routes in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Count @app. and @router. decorators
            app_routes = len(re.findall(r'@app\.[a-z]+\(', content))
            router_routes = len(re.findall(r'@router\.[a-z]+\(', content))
            return app_routes + router_routes
    except Exception:
        return 0

def main():
    """Main progress tracking function"""
    print("Catalynx Modularization Progress Report")
    print("=" * 50)
    
    # Original monolithic file
    main_py_path = Path("src/web/main.py")
    main_py_lines = count_lines_in_file(main_py_path)
    main_py_routes = count_routes_in_file(main_py_path)
    
    print(f"\nORIGINAL MONOLITHIC FILE:")
    print(f"   src/web/main.py: {main_py_lines:,} lines, {main_py_routes} routes")
    
    # Check modularized components
    routers_dir = Path("src/web/routers")
    services_dir = Path("src/web/services")
    
    print(f"\nMODULARIZED COMPONENTS:")
    
    # Services
    total_service_lines = 0
    if services_dir.exists():
        for service_file in services_dir.glob("*.py"):
            if service_file.name != "__init__.py":
                lines = count_lines_in_file(service_file)
                total_service_lines += lines
                print(f"   {service_file}: {lines} lines")
    
    # Routers  
    total_router_lines = 0
    total_router_routes = 0
    if routers_dir.exists():
        for router_file in routers_dir.glob("*.py"):
            if router_file.name != "__init__.py":
                lines = count_lines_in_file(router_file)
                routes = count_routes_in_file(router_file)
                total_router_lines += lines
                total_router_routes += routes
                print(f"   {router_file}: {lines} lines, {routes} routes")
    
    # Progress calculation
    total_extracted_lines = total_service_lines + total_router_lines
    remaining_lines = main_py_lines - total_extracted_lines
    progress_percentage = (total_extracted_lines / main_py_lines) * 100 if main_py_lines > 0 else 0
    
    print(f"\nPROGRESS SUMMARY:")
    print(f"   Lines extracted: {total_extracted_lines:,}")
    print(f"   Lines remaining: {remaining_lines:,}")
    print(f"   Progress: {progress_percentage:.1f}%")
    print(f"   Routes extracted: {total_router_routes}")
    print(f"   Routes remaining: {main_py_routes - total_router_routes}")
    
    # Test modular components
    print(f"\nTESTING MODULAR COMPONENTS:")
    
    try:
        # Test dashboard router
        from src.web.routers.dashboard import router as dashboard_router
        print(f"   [OK] Dashboard router: SUCCESS")
    except Exception as e:
        print(f"   [ERROR] Dashboard router: {e}")
    
    try:
        # Test similarity service
        from src.web.services.similarity_service import get_similarity_service
        service = get_similarity_service()
        test_result = service.are_similar("Test Inc", "Test Inc.")
        print(f"   [OK] Similarity service: SUCCESS (test similarity: {test_result})")
    except Exception as e:
        print(f"   [ERROR] Similarity service: {e}")
    
    # Recommendations
    print(f"\nNEXT STEPS:")
    if progress_percentage < 25:
        print(f"   • Create profiles router (~25 routes)")
        print(f"   • Create discovery router (~30 routes)")
        print(f"   • Extract more utility services")
    elif progress_percentage < 50:
        print(f"   • Create scoring router (~20 routes)")
        print(f"   • Create AI processing router (~15 routes)")
    elif progress_percentage < 75:
        print(f"   • Create export router (~10 routes)")
        print(f"   • Create WebSocket router (~5 routes)")
    else:
        print(f"   • Finalize remaining routes")
        print(f"   • Update main.py to use modular routers")
        print(f"   • Frontend modularization (app.js)")
    
    print(f"\nTARGET: <1,000 lines in main.py (currently {main_py_lines:,} lines)")
    
    return {
        "total_lines": main_py_lines,
        "extracted_lines": total_extracted_lines,
        "progress_percentage": progress_percentage,
        "routes_extracted": total_router_routes,
        "routes_remaining": main_py_routes - total_router_routes
    }

if __name__ == "__main__":
    main()