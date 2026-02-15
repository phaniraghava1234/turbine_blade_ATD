"""
Google Colab Setup Script
==========================

Run this first in Google Colab to set up the environment and install dependencies.

Usage in Colab:
    !python google_colab_setup.py

Then run:
    !python run_complete_workflow.py
"""

import subprocess
import sys
import os

def print_banner(text):
    """Print a formatted banner"""
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70 + "\n")

def install_system_packages():
    """Install system-level packages (C++ compiler, etc.)"""
    print_banner("INSTALLING SYSTEM PACKAGES")
    
    packages = ['g++', 'cmake', 'build-essential']
    
    print("Installing C++ compiler and build tools...")
    try:
        subprocess.run(['apt-get', 'update', '-qq'], check=True)
        subprocess.run(['apt-get', 'install', '-y', '-qq'] + packages, check=True)
        print("✓ System packages installed")
    except Exception as e:
        print(f"Warning: Could not install system packages: {e}")
        print("  (C++ solver compilation may not work)")

def install_python_packages():
    """Install Python dependencies"""
    print_banner("INSTALLING PYTHON PACKAGES")
    
    packages = [
        'numpy',
        'pandas',
        'plotly',
        'gmsh',
        'meshio',
        'kaleido',  # For static image export from plotly
    ]
    
    print("Installing Python packages...")
    for package in packages:
        print(f"  Installing {package}...")
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-q', package],
                check=True,
                capture_output=True
            )
            print(f"  ✓ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed to install {package}: {e}")
    
    print("\n✓ All Python packages installed")

def verify_installation():
    """Verify that all packages are installed correctly"""
    print_banner("VERIFYING INSTALLATION")
    
    # Test Python packages
    python_packages = {
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'plotly': 'Plotly',
        'gmsh': 'Gmsh',
        'meshio': 'MeshIO',
    }
    
    print("Python packages:")
    all_good = True
    for package, name in python_packages.items():
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - MISSING")
            all_good = False
    
    # Test C++ compiler
    print("\nC++ compiler:")
    try:
        result = subprocess.run(
            ['g++', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.split('\n')[0]
        print(f"  ✓ {version}")
    except:
        print(f"  ✗ g++ not found")
        all_good = False
    
    if all_good:
        print("\n✓ All dependencies verified")
    else:
        print("\n⚠ Some dependencies missing - some features may not work")
    
    return all_good

def check_files():
    """Check if all required source files are present"""
    print_banner("CHECKING SOURCE FILES")
    
    required_files = [
        'turbine_blade_design.py',
        'turbine_blade_geometry.py',
        'turbine_blade_mesher.py',
        'turbine_cfd_solver.cpp',
        'turbine_cfd_postprocess.py',
        'run_complete_workflow.py',
        'CMakeLists.txt',
        'README.md'
    ]
    
    all_present = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - MISSING")
            all_present = False
    
    if all_present:
        print("\n✓ All source files present")
    else:
        print("\n⚠ Some source files missing")
        print("  Make sure you've uploaded all files to Colab")
    
    return all_present

def compile_solver():
    """Compile the C++ solver"""
    print_banner("COMPILING C++ SOLVER")
    
    print("Compiling turbine_cfd_solver.cpp...")
    
    try:
        result = subprocess.run(
            ['g++', '-std=c++17', '-O2', '-Wall',
             'turbine_cfd_solver.cpp', '-o', 'turbine_solver'],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ Solver compiled successfully")
        print("  Executable: ./turbine_solver")
        return True
    except subprocess.CalledProcessError as e:
        print("✗ Compilation failed:")
        print(e.stderr)
        print("\n  The Python-only workflow will still work.")
        print("  CFD solver will create synthetic data for post-processing demo.")
        return False

def create_quick_start_notebook():
    """Create a quick start guide"""
    print_banner("QUICK START GUIDE")
    
    guide = """
╔══════════════════════════════════════════════════════════════════════╗
║                         QUICK START GUIDE                            ║
╚══════════════════════════════════════════════════════════════════════╝

Option 1: Run Complete Workflow (Recommended)
──────────────────────────────────────────────
    !python run_complete_workflow.py

This will run all steps automatically:
  1. Blade design from engine parameters
  2. 3D geometry generation  
  3. Mesh generation with gmsh
  4. CFD solver compilation and execution
  5. Post-processing and visualization

Option 2: Run Individual Steps
───────────────────────────────
Step 1 - Blade Design:
    !python turbine_blade_design.py

Step 2 - Geometry Generation:
    !python turbine_blade_geometry.py

Step 3 - Mesh Generation:
    !python turbine_blade_mesher.py

Step 4 - Run CFD Solver:
    !./turbine_solver turbine_blade.cgns

Step 5 - Post-Processing:
    !python turbine_cfd_postprocess.py

Option 3: Use Python API in Notebook
─────────────────────────────────────
    from run_complete_workflow import TurbineWorkflowManager
    
    workflow = TurbineWorkflowManager(
        engine_type='turbofan',  # or 'turbojet'
        altitude=10668,          # meters
        mach=0.85
    )
    
    workflow.run_complete_workflow(display_in_notebook=True)

View Results
────────────
Open the generated HTML files in new tabs:
  • turbine_blade_mesh.html - Interactive mesh visualization
  • cfd_contours.html - Flow field contour plots
  • cfd_3d_visualization.html - 3D flow field
  • cfd_performance.html - Performance analysis

Or in Colab:
    from IPython.display import IFrame
    IFrame(src='turbine_blade_mesh.html', width=1000, height=600)

Customize Parameters
────────────────────
Edit the engine parameters in run_complete_workflow.py or create custom:

    workflow = TurbineWorkflowManager(
        engine_type='turbojet',  # Change to turbojet
        altitude=15000,          # 15 km altitude
        mach=1.5                 # Supersonic
    )

For More Information
────────────────────
See README.md for:
  • Complete documentation
  • References and citations
  • Theoretical background
  • Customization options
  • Troubleshooting

╔══════════════════════════════════════════════════════════════════════╗
║  Ready to run! Execute: !python run_complete_workflow.py            ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    
    print(guide)
    
    # Save to file
    with open('QUICK_START.txt', 'w') as f:
        f.write(guide)
    
    print("\n✓ Quick start guide saved to QUICK_START.txt")

def main():
    """Main setup function"""
    print("\n" + "=" * 70 * 2)
    print("GOOGLE COLAB SETUP - TURBINE BLADE AEROTHERMODYNAMICS")
    print("=" * 70 * 2)
    
    # Install system packages
    install_system_packages()
    
    # Install Python packages
    install_python_packages()
    
    # Verify installation
    verify_installation()
    
    # Check source files
    check_files()
    
    # Compile solver
    compile_solver()
    
    # Create quick start guide
    create_quick_start_notebook()
    
    # Final message
    print("\n" + "=" * 70)
    print("SETUP COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Run the complete workflow:")
    print("       !python run_complete_workflow.py")
    print("\n  2. Or see QUICK_START.txt for more options")
    print("\n  3. Read README.md for full documentation")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
