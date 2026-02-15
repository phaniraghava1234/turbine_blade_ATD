# Turbine Blade Aerothermodynamics Simulation Framework

A complete computational framework for turbine blade design, meshing, CFD simulation, and post-processing. Designed to run in Google Colab or local Python/C++ environment.

## Overview

This framework implements the complete workflow for turbine blade aerothermodynamic analysis:

1. **Blade Design** - Engine cycle analysis and turbine stage design
2. **Geometry Generation** - 3D blade geometry from aerodynamic parameters
3. **Mesh Generation** - CFD mesh using gmsh with boundary layers
4. **CFD Solver** - 3D RANS solver in C++ with k-omega SST turbulence
5. **Post-Processing** - Interactive visualization of results

## References

### Primary References

#### Engine Cycle and Blade Design:
1. **Mattingly, J.D.** (2006). *Elements of Propulsion: Gas Turbines and Rockets*, 2nd Ed., AIAA Education Series
   - Used for: Brayton cycle analysis, compressor/turbine matching, performance calculations
   - Equations: 3.1-3.51 (cycle analysis), 10.23 (annulus sizing)

2. **Mattingly, J.D., Heiser, W.H., Pratt, D.T.** (2002). *Aircraft Engine Design*, 2nd Ed., AIAA
   - Used for: Detailed turbine design methodology, component matching
   - Chapter 5: Engine cycle selection and optimization
   - Chapter 10: Turbomachinery design

3. **Saravanamuttoo, H.I.H., Rogers, G.F.C., Cohen, H., Straznicky, P.V.** (2009). *Gas Turbine Theory*, 6th Ed., Pearson
   - Used for: Velocity triangle analysis, degree of reaction, stage loading
   - Equations: 7.12-7.15 (velocity triangles), 7.28 (Zweifel correlation), 7.44 (free vortex)

4. **Aungier, R.H.** (2006). *Turbine Aerodynamics: Axial-Flow and Radial-Flow Turbine Design and Analysis*, ASME Press
   - Used for: Detailed blade profile design, 3D effects, loss correlations
   - Chapter 3: Mean-line analysis
   - Chapter 4: Blade geometry generation
   - Table 3.1: Design parameter ranges

#### CFD Solver:
5. **Blazek, J.** (2015). *Computational Fluid Dynamics: Principles and Applications*, 3rd Ed., Elsevier
   - Used for: Complete CFD methodology, finite volume discretization
   - Section 3.1: Governing equations (Eq. 3.1, 3.5)
   - Section 4.3: Boundary layer meshing
   - Section 4.4.3: AUSM+ flux scheme

6. **Anderson, J.D.** (1995). *Computational Fluid Dynamics: The Basics with Applications*, McGraw-Hill
   - Used for: Fundamentals of CFD, compressible flow
   - Equation 7.26: Speed of sound calculation

7. **Tannehill, J.C., Anderson, D.A., Pletcher, R.H.** (2012). *Computational Fluid Mechanics and Heat Transfer*, 3rd Ed., Taylor & Francis
   - Used for: Heat transfer modeling, viscosity models
   - Equation 2.37: Sutherland's law

8. **Wilcox, D.C.** (2006). *Turbulence Modeling for CFD*, 3rd Ed., DCW Industries
   - Used for: k-omega SST turbulence model implementation
   - Chapter 4: Two-equation models

9. **Menter, F.R.** (1994). "Two-Equation Eddy-Viscosity Turbulence Models for Engineering Applications", *AIAA Journal*, 32(8), 1598-1605
   - Used for: k-omega SST model constants and formulation

10. **Liou, M.S.** (1996). "A Sequel to AUSM: AUSM+", *Journal of Computational Physics*, 129, 364-382
    - Used for: AUSM+ flux splitting scheme

#### Mesh Generation:
11. **Geuzaine, C. and Remacle, J.F.** (2009). "Gmsh: A 3-D finite element mesh generator with built-in pre- and post-processing facilities", *International Journal for Numerical Methods in Engineering*, 79(11), 1309-1331
    - Used for: Mesh generation methodology

12. **CGNS Documentation** (https://cgns.github.io/)
    - Used for: CFD General Notation System file format

## File Structure

```
.
├── turbine_blade_design.py          # Step 1: Blade design from engine params
├── turbine_blade_geometry.py        # Step 2: 3D geometry generation
├── turbine_blade_mesher.py          # Step 3: Mesh generation with gmsh
├── turbine_cfd_solver.cpp           # Step 4: C++ CFD solver (RANS + k-omega SST)
├── turbine_cfd_postprocess.py       # Step 5: Post-processing and visualization
├── run_complete_workflow.py         # Master script to run all steps
├── CMakeLists.txt                   # Build system for C++ solver
├── google_colab_setup.py            # Google Colab setup script
└── README.md                        # This file
```

## Installation

### Option 1: Google Colab (Recommended)

1. Upload all files to Google Colab or mount Google Drive
2. Run the setup script:

```python
!python google_colab_setup.py
```

3. Run the complete workflow:

```python
!python run_complete_workflow.py
```

### Option 2: Local Installation

#### Prerequisites:
- Python 3.8+
- C++ compiler (g++ or clang++)
- CMake 3.10+ (optional, for building C++ solver)

#### Python Dependencies:

```bash
pip install numpy pandas plotly gmsh meshio
```

#### Compile C++ Solver:

Using CMake:
```bash
mkdir build && cd build
cmake ..
make
```

Or directly:
```bash
g++ -std=c++17 -O2 turbine_cfd_solver.cpp -o turbine_solver
```

## Usage

### Quick Start - Complete Workflow

Run everything automatically:

```python
python run_complete_workflow.py
```

### Step-by-Step Execution

#### Step 1: Blade Design

```python
import turbine_blade_design as tbd

conditions = tbd.EngineOperatingConditions(
    engine_type='turbofan',  # or 'turbojet'
    altitude=10668,          # m (35,000 ft)
    mach_number=0.85,
    thrust_requirement=100000,  # N
    bypass_ratio=9.0
)

designer = tbd.TurbineBladeDesigner(conditions)
design_data = designer.save_design_to_json('turbine_blade_design.json')
```

**Output**: `turbine_blade_design.json` - Contains cycle parameters and blade geometry

#### Step 2: Geometry Generation

```python
import turbine_blade_geometry as tbg

generator = tbg.TurbineBladeGeometry('turbine_blade_design.json')
geometry = generator.save_geometry('turbine_blade_geometry.json')
```

**Output**: `turbine_blade_geometry.json` - Contains 3D point cloud of blade

#### Step 3: Mesh Generation

```python
import turbine_blade_mesher as tbm

mesher = tbm.TurbineBladeMesher('turbine_blade_geometry.json')
mesher.initialize_gmsh()
mesher.create_blade_geometry_gmsh()
mesher.create_flow_domain()
mesher.generate_mesh()
mesher.calculate_mesh_quality()

# Save outputs
mesher.save_mesh_cgns('turbine_blade.cgns')
mesher.create_interactive_visualization('turbine_blade_mesh.html')
mesher.save_quality_metrics('mesh_quality_metrics.json')
mesher.finalize()
```

**Outputs**:
- `turbine_blade.cgns` - Mesh file for CFD solver
- `turbine_blade_mesh.html` - Interactive 3D mesh visualization
- `mesh_quality_metrics.json` - Mesh quality statistics

#### Step 4: Run CFD Solver

```bash
./turbine_solver turbine_blade.cgns
```

**Output**: `turbine_solution.dat` - Flow field solution

#### Step 5: Post-Processing

```python
import turbine_cfd_postprocess as tcp

post = tcp.TurbineCFDPostProcessor('turbine_solution.dat', 'turbine_blade_design.json')
results = post.save_all_visualizations()
```

**Outputs**:
- `cfd_contours.html` - 2D contour plots
- `cfd_3d_visualization.html` - 3D flow field
- `cfd_performance.html` - Performance analysis
- `cfd_metrics.json` - Performance metrics (efficiency, pressure ratio, etc.)

## Output Files

### Design Files
- **turbine_blade_design.json**: Engine cycle parameters, turbine stage design, velocity triangles

### Geometry Files
- **turbine_blade_geometry.json**: 3D blade surface coordinates, twist distribution, airfoil sections

### Mesh Files
- **turbine_blade.cgns**: CFD mesh in CGNS format (industry standard)
- **turbine_blade.vtk**: Mesh in VTK format (for ParaView)
- **turbine_blade_mesh.html**: Interactive mesh visualization (open in browser)
- **mesh_quality_metrics.json**: Mesh statistics (node count, element quality, etc.)

### Solution Files
- **turbine_solution.dat**: CFD solution data (density, velocity, pressure, temperature, Mach)

### Visualization Files (Interactive HTML)
- **cfd_contours.html**: Mid-span slices of Mach, pressure, temperature, velocity
- **cfd_3d_visualization.html**: 3D scatter plot of flow field
- **cfd_performance.html**: Histograms and distributions
- **cfd_metrics.json**: Performance metrics:
  - Pressure ratio
  - Temperature ratio
  - Isentropic efficiency
  - Max Mach number
  - Velocity statistics

## Customization

### Modify Engine Operating Point

Edit in `turbine_blade_design.py` or pass to `TurbineBladeDesigner`:

```python
conditions = tbd.EngineOperatingConditions(
    engine_type='turbojet',     # Change engine type
    altitude=15000,             # Change altitude (m)
    mach_number=1.2,            # Change Mach number
    thrust_requirement=150000,  # Change thrust (N)
    bypass_ratio=0.0            # 0 for turbojet
)
```

### Modify Turbine Design Parameters

In `turbine_blade_design.py`, modify the `design_turbine_stage()` method:

```python
loading_coeff = 2.5     # Increase for higher loading
flow_coeff = 0.7        # Increase for higher flow
reaction = 0.5          # Change degree of reaction
```

### Modify Mesh Resolution

In `turbine_blade_mesher.py`:

```python
self.mesh_size_blade = self.geometry['chord'] / 50  # Finer mesh
self.mesh_size_farfield = self.geometry['chord'] * 1  # Smaller domain
```

### Modify CFD Solver Settings

In `turbine_cfd_solver.cpp`:

```cpp
CFL = 0.8;                  // Courant number
maxIterations = 5000;       // More iterations
residualTarget = 1e-8;      // Tighter convergence
```

## Theoretical Background

### Engine Cycle

The Brayton cycle for gas turbines (Mattingly, Ch. 3):

1. **Compression**: 
   - τ_c = π_c^((γ-1)/γ/η_c)
   - T_03 = T_02 × τ_c

2. **Combustion**:
   - T_04 = TIT (Turbine Inlet Temperature)

3. **Turbine Expansion**:
   - Power balance: W_turbine = W_compressor + W_fan
   - τ_t = 1 - W_compressor/(c_p × T_04)

### Turbine Stage Design

Mean-line analysis (Saravanamuttoo, Ch. 7):

**Velocity Triangles**:
- U = ω × r_mean (Blade speed)
- V = Absolute velocity
- W = Relative velocity = V - U

**Loading Coefficient**:
ψ = ΔH₀/U² = (V_θ1 + V_θ2)/U

**Flow Coefficient**:
φ = V_x/U

**Degree of Reaction**:
R = 1 - (V_θ1 + V_θ2)/(2U)

### CFD Solver

**Governing Equations** - 3D Compressible RANS:

∂Q/∂t + ∇·F = 0

Where:
- Q = [ρ, ρu, ρv, ρw, ρE]ᵀ (Conservative variables)
- F = Inviscid + Viscous fluxes

**Turbulence Model** - k-omega SST (Menter, 1994):
- Combines k-epsilon in freestream with k-omega near walls
- Production, dissipation, and cross-diffusion terms

**Numerical Method**:
- Spatial discretization: Finite volume method
- Flux scheme: AUSM+ (Liou, 1996)
- Time integration: Explicit Euler with local time stepping

## Validation

The framework implements well-established methods from the literature:

1. **Cycle Analysis**: Validated against Mattingly examples (Elements of Propulsion, Ch. 3)
2. **Velocity Triangles**: Standard turbomachinery theory (Saravanamuttoo)
3. **CFD Solver**: Based on industry-standard methods (Blazek, Anderson)
4. **Turbulence Model**: k-omega SST is widely validated (Menter, 1994)

For production use, results should be validated against:
- Experimental data
- High-fidelity commercial CFD (ANSYS Fluent, STAR-CCM+)
- Test rig measurements

## Limitations

1. **Simplified Geometry**: Uses NACA-like profiles instead of true turbine airfoils
2. **Steady-State**: No transient effects or rotor-stator interaction
3. **Single Blade Passage**: No full annulus simulation
4. **Cooling**: Blade cooling not modeled
5. **Material**: Thermal and mechanical stress not computed
6. **Solver**: Simplified compared to commercial CFD:
   - Explicit time integration only
   - Basic AUSM+ flux without higher-order reconstruction
   - No advanced turbulence models (DES, LES)

## Future Enhancements

- [ ] Full 3D multi-blade row simulation
- [ ] Unsteady RANS for rotor-stator interaction
- [ ] Blade cooling modeling (film cooling, internal cooling)
- [ ] Thermal and stress analysis
- [ ] Optimization loop (adjoint methods)
- [ ] Real turbine blade profiles (GE E3, CFM56, etc.)
- [ ] Implicit time integration for faster convergence
- [ ] Parallel computing (MPI)

## Troubleshooting

### Mesh generation fails
- Try the simplified test mesh: `create_simple_test_mesh()` in mesher
- Reduce mesh resolution
- Check geometry JSON for valid coordinates

### C++ compilation fails
- Install g++: `apt-get install g++` (Colab) or `brew install gcc` (Mac)
- Check C++ standard: requires C++17
- Use alternative compiler: `clang++ -std=c++17 ...`

### Solver doesn't converge
- Reduce CFL number (< 0.5)
- Check boundary conditions
- Verify mesh quality
- Initialize with better guess

### Visualization not showing
- Open HTML files directly in browser
- Check file paths
- Verify plotly installation

## Citation

If you use this code, please cite the primary references above, particularly:

- Mattingly (2006) for engine cycle analysis
- Saravanamuttoo (2009) for turbine stage design
- Blazek (2015) for CFD methodology
- Menter (1994) for turbulence modeling

## License

Educational and research use. For commercial applications, verify compliance with reference materials and obtain appropriate licenses for third-party libraries (gmsh, CGNS, etc.).

## Author

Created as a comprehensive educational tool for turbine blade aerothermodynamics.

## Contact

For questions or issues, please refer to the original references or consult with subject matter experts in turbomachinery and CFD.

---

**Disclaimer**: This is an educational framework. Production turbine design requires extensive validation, testing, and expertise in turbomachinery, materials science, and mechanical engineering. Always consult qualified engineers and validate against experimental data.
