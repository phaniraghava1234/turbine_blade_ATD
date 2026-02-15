"""
Turbine Blade Aerothermodynamics - Complete Usage Example
==========================================================

This script demonstrates the complete workflow with detailed explanations.
Can be run as a standalone script or imported into a Jupyter notebook.

Author: Educational Framework
References: See README.md for complete citations
"""

# ============================================================================
# IMPORTS
# ============================================================================

import sys
import os
import json
import numpy as np
import pandas as pd

# Import our custom modules
import turbine_blade_design as tbd
import turbine_blade_geometry as tbg
import turbine_blade_mesher as tbm
import turbine_cfd_postprocess as tcp

# For notebook display
try:
    from IPython.display import display, HTML, IFrame
    IN_NOTEBOOK = True
except:
    IN_NOTEBOOK = False

# ============================================================================
# EXAMPLE 1: HIGH-BYPASS TURBOFAN (MODERN COMMERCIAL ENGINE)
# ============================================================================

def example_1_turbofan():
    """
    Example 1: High-Bypass Turbofan
    
    Represents a modern commercial turbofan engine like CFM LEAP or PW1000G
    Operating at typical cruise conditions (35,000 ft, Mach 0.85)
    
    Reference: Mattingly, Aircraft Engine Design (2002), Ch. 2
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: HIGH-BYPASS TURBOFAN")
    print("=" * 70)
    print("\nTypical application: Boeing 737 MAX, Airbus A320neo")
    print("Similar to: CFM LEAP-1B, PW1127G")
    print("-" * 70)
    
    # Define operating conditions
    conditions = tbd.EngineOperatingConditions(
        engine_type='turbofan',
        altitude=10668,           # m (35,000 ft - typical cruise)
        mach_number=0.85,         # Typical cruise Mach
        thrust_requirement=120000, # N (27,000 lbf)
        bypass_ratio=9.0          # Modern high-bypass
    )
    
    print("\nEngine Parameters:")
    print(f"  Type: {conditions.engine_type.upper()}")
    print(f"  Bypass Ratio: {conditions.bypass_ratio}")
    print(f"  Cruise Altitude: {conditions.altitude/1000:.1f} km ({conditions.altitude/0.3048:.0f} ft)")
    print(f"  Cruise Mach: {conditions.mach_number}")
    print(f"  Required Thrust: {conditions.thrust_requirement/1000:.1f} kN ({conditions.thrust_requirement/4.448:.0f} lbf)")
    
    # Step 1: Design the turbine blade
    print("\n" + "-" * 70)
    print("Step 1: Turbine Stage Design")
    print("-" * 70)
    
    designer = tbd.TurbineBladeDesigner(conditions)
    design_data = designer.save_design_to_json('example1_turbofan_design.json')
    
    # Extract key results
    cycle = design_data['cycle_parameters']
    stage = design_data['stage_parameters']
    
    print(f"\nKey Results:")
    print(f"  Turbine Inlet Temperature: {cycle['T04']:.0f} K ({cycle['T04']*9/5-459.67:.0f} °F)")
    print(f"  Pressure Ratio: {cycle['pressure_ratio']:.2f}")
    print(f"  Specific Work: {cycle['specific_work']/1000:.1f} kJ/kg")
    print(f"  Blade Speed: {stage['U']:.1f} m/s")
    print(f"  Flow Coefficient: {stage['flow_coefficient']:.3f}")
    print(f"  Loading Coefficient: {stage['loading_coefficient']:.3f}")
    print(f"  Number of Blades: {stage['num_blades']}")
    
    # Step 2: Generate geometry
    print("\n" + "-" * 70)
    print("Step 2: 3D Blade Geometry Generation")
    print("-" * 70)
    
    generator = tbg.TurbineBladeGeometry('example1_turbofan_design.json')
    geometry = generator.save_geometry('example1_turbofan_geometry.json')
    
    print(f"\nGeometry Details:")
    print(f"  Hub Radius: {geometry['radius_hub']*1000:.1f} mm")
    print(f"  Tip Radius: {geometry['radius_tip']*1000:.1f} mm")
    print(f"  Blade Height: {(geometry['radius_tip']-geometry['radius_hub'])*1000:.1f} mm")
    print(f"  Aspect Ratio: {(geometry['radius_tip']-geometry['radius_hub'])/geometry['chord']:.2f}")
    
    return design_data, geometry

# ============================================================================
# EXAMPLE 2: TURBOJET (SUPERSONIC FIGHTER/OLDER DESIGN)
# ============================================================================

def example_2_turbojet():
    """
    Example 2: Turbojet Engine
    
    Represents a turbojet engine for supersonic flight
    Similar to early commercial jets or modern military engines
    
    Reference: Mattingly, Elements of Propulsion (2006), Ch. 3
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: TURBOJET ENGINE")
    print("=" * 70)
    print("\nTypical application: F-16 (early models), Boeing 707")
    print("Similar to: J79, JT3D (without bypass)")
    print("-" * 70)
    
    conditions = tbd.EngineOperatingConditions(
        engine_type='turbojet',
        altitude=12000,           # m (40,000 ft)
        mach_number=1.5,          # Supersonic
        thrust_requirement=80000,  # N
        bypass_ratio=0.0          # Pure turbojet
    )
    
    print("\nEngine Parameters:")
    print(f"  Type: {conditions.engine_type.upper()}")
    print(f"  Bypass Ratio: {conditions.bypass_ratio} (pure jet)")
    print(f"  Altitude: {conditions.altitude/1000:.1f} km")
    print(f"  Mach: {conditions.mach_number} (supersonic)")
    
    designer = tbd.TurbineBladeDesigner(conditions)
    design_data = designer.save_design_to_json('example2_turbojet_design.json')
    
    return design_data

# ============================================================================
# EXAMPLE 3: MESH QUALITY ANALYSIS
# ============================================================================

def example_3_mesh_analysis():
    """
    Example 3: Detailed Mesh Generation and Quality Analysis
    
    Demonstrates mesh generation with quality metrics
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: MESH GENERATION AND QUALITY ANALYSIS")
    print("=" * 70)
    
    # Use the turbofan design from Example 1
    if not os.path.exists('example1_turbofan_geometry.json'):
        print("\nGenerating required geometry...")
        example_1_turbofan()
    
    print("\nGenerating CFD mesh...")
    
    mesher = tbm.TurbineBladeMesher('example1_turbofan_geometry.json')
    mesher.initialize_gmsh()
    
    try:
        mesher.create_blade_geometry_gmsh()
        mesher.create_flow_domain()
        mesher.create_boundary_layer_mesh()
        mesher.generate_mesh()
        mesher.calculate_mesh_quality()
        
        mesher.save_mesh_cgns('example3_mesh.cgns')
        mesher.save_mesh_vtk('example3_mesh.vtk')
        fig = mesher.create_interactive_visualization('example3_mesh_viz.html')
        mesher.save_quality_metrics('example3_mesh_quality.json')
        
        # Display quality metrics
        print("\n" + "-" * 70)
        print("Mesh Quality Metrics")
        print("-" * 70)
        
        with open('example3_mesh_quality.json', 'r') as f:
            metrics = json.load(f)
        
        print(f"  Total Nodes: {metrics.get('num_nodes', 'N/A'):,}")
        print(f"  Total Elements: {metrics.get('num_elements', 'N/A'):,}")
        print(f"  Min Quality: {metrics.get('min_quality', 'N/A')}")
        print(f"  Mean Quality: {metrics.get('mean_quality', 'N/A')}")
        print(f"  Poor Elements (<0.3): {metrics.get('poor_elements', 0)} ({metrics.get('poor_percentage', 0):.2f}%)")
        
    except Exception as e:
        print(f"Complex meshing failed: {e}")
        print("Creating simplified mesh...")
        metrics, fig = tbm.create_simple_test_mesh()
    
    mesher.finalize()
    
    print(f"\n✓ Mesh visualization: example3_mesh_viz.html")
    
    if IN_NOTEBOOK:
        display(HTML("<h3>Interactive Mesh Visualization</h3>"))
        display(IFrame(src='example3_mesh_viz.html', width=1000, height=600))
    
    return metrics

# ============================================================================
# EXAMPLE 4: POST-PROCESSING AND ANALYSIS
# ============================================================================

def example_4_postprocessing():
    """
    Example 4: Comprehensive Post-Processing
    
    Demonstrates flow field visualization and performance analysis
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: POST-PROCESSING AND PERFORMANCE ANALYSIS")
    print("=" * 70)
    
    # Create post-processor (will generate synthetic data if no solution exists)
    post = tcp.TurbineCFDPostProcessor(
        'turbine_solution.dat',
        'example1_turbofan_design.json'
    )
    
    print("\nGenerating visualizations...")
    results = post.save_all_visualizations(output_dir='.')
    
    # Display results
    print("\n" + "-" * 70)
    print("Generated Visualizations")
    print("-" * 70)
    print("  ✓ cfd_contours.html - Flow field contours")
    print("  ✓ cfd_3d_visualization.html - 3D flow field")
    print("  ✓ cfd_performance.html - Performance histograms")
    print("  ✓ cfd_metrics.json - Performance metrics")
    
    # Display key metrics
    metrics = results['metrics']
    
    print("\n" + "-" * 70)
    print("Performance Metrics")
    print("-" * 70)
    print(f"  Max Mach Number: {metrics.get('max_mach', 0):.3f}")
    print(f"  Avg Mach Number: {metrics.get('avg_mach', 0):.3f}")
    print(f"  Max Velocity: {metrics.get('max_velocity', 0):.1f} m/s")
    print(f"  Max Temperature: {metrics.get('max_temperature', 0):.1f} K")
    
    if 'pressure_ratio' in metrics:
        print(f"  Pressure Ratio: {metrics['pressure_ratio']:.3f}")
        print(f"  Temperature Ratio: {metrics['temperature_ratio']:.3f}")
        print(f"  Isentropic Efficiency: {metrics.get('isentropic_efficiency', 0)*100:.1f}%")
    
    # Display in notebook if possible
    if IN_NOTEBOOK:
        print("\nDisplaying interactive plots in notebook...")
        
        display(HTML("<h2>Flow Field Contours</h2>"))
        display(IFrame(src='cfd_contours.html', width=1200, height=800))
        
        display(HTML("<h2>3D Flow Visualization</h2>"))
        display(IFrame(src='cfd_3d_visualization.html', width=1000, height=800))
        
        display(HTML("<h2>Performance Analysis</h2>"))
        display(IFrame(src='cfd_performance.html', width=1200, height=800))
    
    return results

# ============================================================================
# EXAMPLE 5: PARAMETRIC STUDY
# ============================================================================

def example_5_parametric_study():
    """
    Example 5: Parametric Study
    
    Vary design parameters and observe effects
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: PARAMETRIC STUDY - BYPASS RATIO EFFECTS")
    print("=" * 70)
    print("\nComparing different bypass ratios:")
    print("  BPR = 0 (pure turbojet)")
    print("  BPR = 5 (low bypass turbofan)")
    print("  BPR = 9 (high bypass turbofan)")
    print("-" * 70)
    
    results = []
    
    for bpr in [0, 5, 9]:
        engine_type = 'turbojet' if bpr == 0 else 'turbofan'
        
        conditions = tbd.EngineOperatingConditions(
            engine_type=engine_type,
            altitude=10668,
            mach_number=0.85,
            thrust_requirement=100000,
            bypass_ratio=bpr
        )
        
        designer = tbd.TurbineBladeDesigner(conditions)
        design = designer.calculate_cycle_parameters()
        stage = designer.design_turbine_stage(design)
        
        results.append({
            'BPR': bpr,
            'TIT': design.T04,
            'Pressure_Ratio': design.pressure_ratio,
            'Specific_Work': design.specific_work,
            'Blade_Speed': stage.U,
            'Flow_Coeff': stage.flow_coefficient,
            'Loading_Coeff': stage.loading_coefficient
        })
    
    # Display as table
    df = pd.DataFrame(results)
    
    print("\nResults:")
    print(df.to_string(index=False))
    
    print("\nObservations:")
    print("  • Higher BPR → Lower turbine inlet temperature")
    print("  • Higher BPR → Lower specific work (less work per unit mass)")
    print("  • Design parameters adjust to maintain thrust requirement")
    
    return df

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def run_all_examples():
    """Run all examples in sequence"""
    print("\n" + "=" * 140)
    print("TURBINE BLADE AEROTHERMODYNAMICS - COMPLETE EXAMPLES")
    print("=" * 140)
    print("\nThis script demonstrates all capabilities of the framework.")
    print("Each example builds on previous ones and demonstrates different aspects.")
    print("\nReferences:")
    print("  • Mattingly - Elements of Propulsion & Aircraft Engine Design")
    print("  • Saravanamuttoo - Gas Turbine Theory")
    print("  • Aungier - Turbine Aerodynamics")
    print("  • Blazek - Computational Fluid Dynamics")
    print("=" * 140)
    
    # Run examples
    try:
        design1, geom1 = example_1_turbofan()
        design2 = example_2_turbojet()
        mesh_metrics = example_3_mesh_analysis()
        post_results = example_4_postprocessing()
        parametric_df = example_5_parametric_study()
        
        print("\n" + "=" * 70)
        print("ALL EXAMPLES COMPLETE!")
        print("=" * 70)
        print("\nGenerated Files:")
        print("  Design: example1_turbofan_design.json, example2_turbojet_design.json")
        print("  Geometry: example1_turbofan_geometry.json")
        print("  Mesh: example3_mesh.cgns, example3_mesh_viz.html")
        print("  CFD Results: cfd_contours.html, cfd_3d_visualization.html, cfd_performance.html")
        print("  Metrics: example3_mesh_quality.json, cfd_metrics.json")
        print("\nOpen the HTML files in a browser to view interactive visualizations!")
        print("=" * 70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_examples()
    sys.exit(0 if success else 1)
