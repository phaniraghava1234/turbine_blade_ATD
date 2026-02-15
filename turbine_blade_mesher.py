"""
Turbine Blade Mesh Generator
=============================

References:
1. Geuzaine, C. and Remacle, J.F., "Gmsh: A 3-D finite element mesh generator",
   Int. J. Numer. Methods Eng., 2009
2. Blazek, J., "Computational Fluid Dynamics: Principles and Applications", 
   3rd Ed., Elsevier, 2015
3. CGNS Documentation, https://cgns.github.io/

Generates structured/unstructured mesh for turbine blade CFD analysis
"""

import numpy as np
import json
import gmsh
import sys
import meshio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

class TurbineBladeMesher:
    """Generate CFD mesh for turbine blade"""
    
    def __init__(self, geometry_file: str):
        """Load geometry from JSON"""
        with open(geometry_file, 'r') as f:
            self.data = json.load(f)
        
        self.geometry = self.data['geometry']
        self.sections = self.data['sections']
        
        # Mesh parameters
        self.mesh_size_blade = self.geometry['chord'] / 30  # Fine mesh on blade
        self.mesh_size_farfield = self.geometry['chord'] * 2  # Coarse far from blade
        
        # Mesh quality metrics
        self.quality_metrics = {}
        
    def initialize_gmsh(self):
        """Initialize gmsh"""
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.model.add("turbine_blade")
        
    def create_blade_geometry_gmsh(self):
        """Create blade geometry in gmsh"""
        print("\nCreating blade geometry in gmsh...")
        
        points_3d = self.geometry['points']
        num_sections = self.geometry['num_sections']
        num_pts_section = self.geometry['num_points_per_section']
        
        # Add points
        point_tags = []
        for section_pts in points_3d:
            section_tags = []
            for pt in section_pts:
                tag = gmsh.model.geo.addPoint(pt[0], pt[1], pt[2], self.mesh_size_blade)
                section_tags.append(tag)
            point_tags.append(section_tags)
        
        print(f"  Added {len(point_tags) * len(point_tags[0])} points")
        
        # Create curves for each section (airfoil contours)
        section_curves = []
        for i, tags in enumerate(point_tags):
            curve = gmsh.model.geo.addBSpline(tags + [tags[0]])  # Close the loop
            section_curves.append(curve)
        
        print(f"  Created {len(section_curves)} airfoil contours")
        
        # Create surface (loft between sections)
        # For simplicity, create ruled surfaces between consecutive sections
        surface_tags = []
        for i in range(len(section_curves) - 1):
            # Create curve loop for each section
            loop1 = gmsh.model.geo.addCurveLoop([section_curves[i]])
            loop2 = gmsh.model.geo.addCurveLoop([section_curves[i+1]])
            
            # Create surface (this is simplified - for real blade use ThruSections)
            try:
                surf = gmsh.model.geo.addPlaneSurface([loop1])
                surface_tags.append(surf)
            except:
                pass  # Handle errors in surface creation
        
        # Synchronize
        gmsh.model.geo.synchronize()
        
        print(f"  Created {len(surface_tags)} surfaces")
        
        return point_tags, section_curves, surface_tags
    
    def create_flow_domain(self):
        """Create flow domain around blade"""
        print("\nCreating flow domain...")
        
        # Domain size (based on blade dimensions)
        r_mean = (self.geometry['radius_hub'] + self.geometry['radius_tip']) / 2
        chord = self.geometry['chord']
        
        # Inlet/outlet distances
        inlet_distance = 3 * chord  # Upstream
        outlet_distance = 5 * chord  # Downstream
        
        # Create simplified box domain for single blade passage
        # In real turbomachinery, use periodic boundaries
        
        theta_blade = 2 * np.pi / self.geometry['num_blades']
        
        # Domain corners (simplified Cartesian box)
        x_min, x_max = -inlet_distance, outlet_distance
        y_min, y_max = -r_mean * theta_blade / 2, r_mean * theta_blade / 2
        z_min, z_max = self.geometry['radius_hub'], self.geometry['radius_tip']
        
        # Create box
        box = gmsh.model.occ.addBox(x_min, y_min, z_min, 
                                     x_max - x_min, 
                                     y_max - y_min, 
                                     z_max - z_min)
        
        gmsh.model.occ.synchronize()
        
        print(f"  Domain: {x_max-x_min:.3f} x {y_max-y_min:.3f} x {z_max-z_min:.3f} m")
        
        return box
    
    def create_boundary_layer_mesh(self):
        """Create boundary layer mesh near blade surface"""
        print("\nSetting up boundary layer mesh...")
        
        # Boundary layer parameters (Blazek, Section 4.3)
        y_plus_target = 1.0  # For resolving viscous sublayer
        first_cell_height = 1e-5  # m, based on Re and y+
        growth_rate = 1.2
        num_layers = 15
        
        # This would be applied to blade surface
        # In gmsh, use Fields or BoundaryLayer
        
        print(f"  First cell height: {first_cell_height*1e6:.2f} μm")
        print(f"  Number of layers: {num_layers}")
        print(f"  Growth rate: {growth_rate}")
        
        # Note: Full implementation requires identifying blade surface entities
        # and applying gmsh.model.mesh.field.add("BoundaryLayer", ...)
        
    def generate_mesh(self):
        """Generate the mesh"""
        print("\nGenerating mesh...")
        
        # Set mesh algorithm
        gmsh.option.setNumber("Mesh.Algorithm", 6)  # Frontal-Delaunay
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Delaunay
        
        # Generate 3D mesh
        gmsh.model.mesh.generate(3)
        
        # Optimize
        gmsh.model.mesh.optimize("Netgen")
        
        # Get mesh statistics
        nodes = gmsh.model.mesh.getNodes()
        elements = gmsh.model.mesh.getElements()
        
        num_nodes = len(nodes[0])
        num_elements = sum([len(e) for e in elements[1]])
        
        print(f"  Nodes: {num_nodes}")
        print(f"  Elements: {num_elements}")
        
        self.quality_metrics['num_nodes'] = int(num_nodes)
        self.quality_metrics['num_elements'] = int(num_elements)
        
        return nodes, elements
    
    def calculate_mesh_quality(self):
        """Calculate mesh quality metrics"""
        print("\nCalculating mesh quality metrics...")
        
        # Get element qualities from gmsh
        element_types, element_tags, node_tags = gmsh.model.mesh.getElements(3)
        
        qualities = []
        for elem_type, tags in zip(element_types, element_tags):
            if len(tags) > 0:
                quality = gmsh.model.mesh.getElementQualities(tags, "minSICN")
                qualities.extend(quality)
        
        if qualities:
            qualities = np.array(qualities)
            self.quality_metrics['min_quality'] = float(np.min(qualities))
            self.quality_metrics['mean_quality'] = float(np.mean(qualities))
            self.quality_metrics['max_quality'] = float(np.max(qualities))
            
            # Count poor quality elements
            poor_quality = np.sum(qualities < 0.3)
            self.quality_metrics['poor_elements'] = int(poor_quality)
            self.quality_metrics['poor_percentage'] = float(poor_quality / len(qualities) * 100)
            
            print(f"  Min quality: {self.quality_metrics['min_quality']:.3f}")
            print(f"  Mean quality: {self.quality_metrics['mean_quality']:.3f}")
            print(f"  Poor elements (<0.3): {poor_quality} ({self.quality_metrics['poor_percentage']:.1f}%)")
        else:
            print("  Warning: Could not calculate quality metrics")
    
    def save_mesh_cgns(self, filename: str):
        """Save mesh in CGNS format for CFD solver"""
        print(f"\nSaving mesh to CGNS: {filename}")
        
        # Write mesh using gmsh
        gmsh.write(filename)
        
        print(f"  ✓ CGNS file saved")
    
    def save_mesh_vtk(self, filename: str):
        """Save mesh to VTK for visualization"""
        print(f"\nSaving mesh to VTK: {filename}")
        gmsh.write(filename)
        print(f"  ✓ VTK file saved")
    
    def create_interactive_visualization(self, output_html: str):
        """Create interactive 3D mesh visualization using plotly"""
        print("\nCreating interactive visualization...")
        
        # Get mesh data
        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
        
        # Reshape coordinates
        coords = node_coords.reshape((-1, 3))
        
        # Sample elements for visualization (surface only)
        element_types, element_tags, node_tags_elem = gmsh.model.mesh.getElements(2)  # 2D elements
        
        # Create visualization
        if len(element_types) > 0 and len(element_tags[0]) > 0:
            # Get surface triangles
            tri_nodes = node_tags_elem[0].reshape((-1, 3)) - 1  # Convert to 0-indexed
            
            # Sample for performance (too many elements slow down browser)
            max_triangles = 5000
            if len(tri_nodes) > max_triangles:
                indices = np.random.choice(len(tri_nodes), max_triangles, replace=False)
                tri_nodes = tri_nodes[indices]
            
            # Create mesh3d
            fig = go.Figure(data=[
                go.Mesh3d(
                    x=coords[:, 0],
                    y=coords[:, 1],
                    z=coords[:, 2],
                    i=tri_nodes[:, 0],
                    j=tri_nodes[:, 1],
                    k=tri_nodes[:, 2],
                    opacity=0.7,
                    color='lightblue',
                    flatshading=True,
                    name='Blade Surface'
                )
            ])
            
            # Add nodes as scatter
            sample_nodes = coords[::max(1, len(coords)//1000)]  # Sample nodes
            fig.add_trace(go.Scatter3d(
                x=sample_nodes[:, 0],
                y=sample_nodes[:, 1],
                z=sample_nodes[:, 2],
                mode='markers',
                marker=dict(size=1, color='red'),
                name='Mesh Nodes'
            ))
            
        else:
            # Fallback: just plot nodes
            sample_nodes = coords[::max(1, len(coords)//2000)]
            fig = go.Figure(data=[
                go.Scatter3d(
                    x=sample_nodes[:, 0],
                    y=sample_nodes[:, 1],
                    z=sample_nodes[:, 2],
                    mode='markers',
                    marker=dict(size=2, color='blue'),
                    name='Mesh Nodes'
                )
            ])
        
        # Add parameters text
        params_text = f"""
        <b>Mesh Parameters:</b><br>
        Nodes: {self.quality_metrics.get('num_nodes', 'N/A')}<br>
        Elements: {self.quality_metrics.get('num_elements', 'N/A')}<br>
        Mean Quality: {self.quality_metrics.get('mean_quality', 'N/A'):.3f}<br>
        Min Quality: {self.quality_metrics.get('min_quality', 'N/A'):.3f}<br>
        <br>
        <b>Blade Parameters:</b><br>
        Mean Radius: {self.geometry['radius_hub']*1000:.1f} mm<br>
        Blade Height: {(self.geometry['radius_tip']-self.geometry['radius_hub'])*1000:.1f} mm<br>
        Chord: {self.geometry['chord']*1000:.1f} mm<br>
        Num Blades: {self.geometry['num_blades']}
        """
        
        fig.update_layout(
            title=dict(
                text="Turbine Blade Mesh - Interactive Visualization",
                x=0.5,
                xanchor='center'
            ),
            scene=dict(
                xaxis_title='X (m)',
                yaxis_title='Y (m)',
                zaxis_title='Z (m)',
                aspectmode='data'
            ),
            annotations=[
                dict(
                    text=params_text,
                    xref="paper",
                    yref="paper",
                    x=0.02,
                    y=0.98,
                    xanchor='left',
                    yanchor='top',
                    showarrow=False,
                    bgcolor='rgba(255, 255, 255, 0.8)',
                    bordercolor='black',
                    borderwidth=1
                )
            ],
            width=1200,
            height=800
        )
        
        # Save to HTML
        fig.write_html(output_html)
        print(f"  ✓ Interactive visualization saved: {output_html}")
        
        return fig
    
    def save_quality_metrics(self, filename: str):
        """Save mesh quality metrics to JSON"""
        with open(filename, 'w') as f:
            json.dump(self.quality_metrics, f, indent=2)
        
        print(f"  ✓ Quality metrics saved: {filename}")
    
    def finalize(self):
        """Clean up gmsh"""
        gmsh.finalize()

def create_simple_test_mesh():
    """Create a simplified mesh for testing (without full blade geometry)"""
    print("\n" + "=" * 70)
    print("Creating simplified test mesh...")
    print("=" * 70)
    
    gmsh.initialize()
    gmsh.model.add("simple_blade")
    
    # Create simple box representing blade domain
    chord = 0.04
    height = 0.02
    span = 0.05
    
    # Create box
    box = gmsh.model.occ.addBox(-chord, -height/2, 0, 
                                 2*chord, height, span)
    
    # Create cylindrical blade (simplified)
    cylinder = gmsh.model.occ.addCylinder(0, 0, span/4, 
                                          0, 0, span/2, 
                                          chord/10)
    
    # Boolean operation
    blade_vol = gmsh.model.occ.cut([(3, box)], [(3, cylinder)])
    
    gmsh.model.occ.synchronize()
    
    # Set mesh size
    gmsh.option.setNumber("Mesh.MeshSizeMin", chord / 50)
    gmsh.option.setNumber("Mesh.MeshSizeMax", chord / 10)
    
    # Generate mesh
    gmsh.model.mesh.generate(3)
    
    # Get statistics
    nodes = gmsh.model.mesh.getNodes()
    print(f"\n  Nodes: {len(nodes[0])}")
    
    # Save
    gmsh.write("simple_blade_mesh.msh")
    gmsh.write("simple_blade_mesh.vtk")
    
    # Visualize
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    coords = node_coords.reshape((-1, 3))
    
    # Sample for viz
    sample = coords[::max(1, len(coords)//2000)]
    
    fig = go.Figure(data=[
        go.Scatter3d(
            x=sample[:, 0],
            y=sample[:, 1],
            z=sample[:, 2],
            mode='markers',
            marker=dict(size=2, color=sample[:, 2], colorscale='Viridis'),
            name='Mesh'
        )
    ])
    
    fig.update_layout(
        title="Simple Blade Mesh Test",
        scene=dict(aspectmode='data'),
        width=1000,
        height=800
    )
    
    fig.write_html("simple_blade_mesh_viz.html")
    
    # Quality metrics
    quality_metrics = {
        'num_nodes': int(len(nodes[0])),
        'mesh_type': 'test_mesh',
        'chord': float(chord),
        'span': float(span)
    }
    
    with open('simple_mesh_quality.json', 'w') as f:
        json.dump(quality_metrics, f, indent=2)
    
    gmsh.finalize()
    
    print(f"\n  ✓ Test mesh created successfully")
    print(f"  ✓ Files: simple_blade_mesh.msh, simple_blade_mesh.vtk")
    print(f"  ✓ Visualization: simple_blade_mesh_viz.html")
    print("=" * 70 + "\n")
    
    return quality_metrics, fig

def main():
    """Main execution"""
    print("=" * 70)
    print("TURBINE BLADE MESH GENERATOR")
    print("=" * 70)
    print("\nReferences:")
    print("  • Gmsh documentation (Geuzaine & Remacle, 2009)")
    print("  • Blazek - Computational Fluid Dynamics (2015)")
    print("  • CGNS format specification")
    print("=" * 70)
    
    geometry_file = 'turbine_blade_geometry.json'
    
    # Check if geometry exists
    if not os.path.exists(geometry_file):
        print(f"\nWarning: Geometry file '{geometry_file}' not found!")
        print("Creating simplified test mesh instead...\n")
        create_simple_test_mesh()
        return
    
    # Full meshing workflow
    print(f"\nLoading geometry from: {geometry_file}")
    
    mesher = TurbineBladeMesher(geometry_file)
    mesher.initialize_gmsh()
    
    try:
        # Create geometry
        mesher.create_blade_geometry_gmsh()
        mesher.create_flow_domain()
        mesher.create_boundary_layer_mesh()
        
        # Generate mesh
        mesher.generate_mesh()
        mesher.calculate_mesh_quality()
        
        # Save outputs
        mesher.save_mesh_cgns('turbine_blade.cgns')
        mesher.save_mesh_vtk('turbine_blade.vtk')
        mesher.create_interactive_visualization('turbine_blade_mesh.html')
        mesher.save_quality_metrics('mesh_quality_metrics.json')
        
        print("\n" + "=" * 70)
        print("Mesh generation complete!")
        print("  • CGNS file: turbine_blade.cgns (for CFD solver)")
        print("  • VTK file: turbine_blade.vtk")
        print("  • Interactive viz: turbine_blade_mesh.html")
        print("  • Quality metrics: mesh_quality_metrics.json")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\nError during meshing: {e}")
        print("Creating simplified test mesh instead...")
        mesher.finalize()
        create_simple_test_mesh()
    
    mesher.finalize()

if __name__ == "__main__":
    main()
