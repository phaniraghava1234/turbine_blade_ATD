"""
Turbine Blade Geometry Generator
=================================

References:
1. Geuzaine, C. and Remacle, J.F., "Gmsh: A 3-D finite element mesh generator 
   with built-in pre- and post-processing facilities", International Journal 
   for Numerical Methods in Engineering, 2009
2. Aungier, R.H., "Turbine Aerodynamics", ASME Press, 2006
3. NACA airfoil database and theory

This code generates 3D turbine blade geometry from design parameters
"""

import numpy as np
import json
import sys
from typing import List, Tuple

class AirfoilGenerator:
    """Generate airfoil coordinates using NACA-like parametric method"""
    
    @staticmethod
    def naca_4_digit_modified(chord: float, thickness: float, camber: float, 
                               num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate modified NACA 4-digit airfoil coordinates
        Adapted for turbine blade profiles
        
        Reference: NACA Technical Report 824 (1945)
        """
        # Chordwise distribution (cosine spacing for better LE/TE resolution)
        beta = np.linspace(0, np.pi, num_points)
        x = chord * (1 - np.cos(beta)) / 2
        
        # Thickness distribution (modified for turbine blades)
        t = thickness * chord
        
        # NACA 4-digit thickness formula
        yt = 5 * t * (
            0.2969 * np.sqrt(x/chord) - 
            0.1260 * (x/chord) - 
            0.3516 * (x/chord)**2 + 
            0.2843 * (x/chord)**3 - 
            0.1015 * (x/chord)**4  # Modified for closed TE
        )
        
        # Camber line (simplified parabolic)
        max_camber = camber * chord / 100  # Convert to meters
        if max_camber > 0:
            yc = 4 * max_camber * (x/chord) * (1 - x/chord)
            dyc_dx = 4 * max_camber / chord * (1 - 2*x/chord)
            theta = np.arctan(dyc_dx)
        else:
            yc = np.zeros_like(x)
            theta = np.zeros_like(x)
        
        # Upper and lower surfaces
        xu = x - yt * np.sin(theta)
        yu = yc + yt * np.cos(theta)
        
        xl = x + yt * np.sin(theta)
        yl = yc - yt * np.cos(theta)
        
        # Combine (LE to TE on upper, TE to LE on lower)
        x_coords = np.concatenate([xu[::-1], xl[1:]])
        y_coords = np.concatenate([yu[::-1], yl[1:]])
        
        return x_coords, y_coords

class TurbineBladeGeometry:
    """Generate 3D turbine blade geometry"""
    
    def __init__(self, design_file: str):
        """Load design from JSON"""
        with open(design_file, 'r') as f:
            self.design = json.load(f)
        
        self.stage = self.design['stage_parameters']
        self.geometry = self.design['blade_geometry']
        
    def generate_blade_sections(self) -> List[dict]:
        """Generate airfoil coordinates for each blade section"""
        print("\nGenerating blade sections...")
        
        sections = []
        for i, section in enumerate(self.geometry['sections']):
            print(f"  Section {i+1}/{len(self.geometry['sections'])}: r={section['radius']*1000:.1f} mm")
            
            # Generate airfoil
            x, y = AirfoilGenerator.naca_4_digit_modified(
                chord=section['chord'],
                thickness=section['thickness_to_chord'],
                camber=section['camber'],
                num_points=100
            )
            
            sections.append({
                'radius': section['radius'],
                'x': x.tolist(),
                'y': y.tolist(),
                'z': 0.0,  # Will be positioned in 3D
                'twist': self.geometry['twist_distribution'][i],
                'lean': self.geometry['lean_angle'][i]
            })
        
        return sections
    
    def create_3d_blade_points(self, sections: List[dict]) -> dict:
        """
        Create 3D point cloud for blade surface
        Using stacking with twist and lean
        """
        print("\nCreating 3D blade geometry...")
        
        all_points = []
        theta_positions = []  # Circumferential positions
        
        for section in sections:
            r = section['radius']
            x_local = np.array(section['x'])
            y_local = np.array(section['y'])
            twist = section['twist'] * np.pi / 180
            lean = section['lean'] * np.pi / 180
            
            # Apply twist (rotation about chord)
            x_twisted = x_local * np.cos(twist) - y_local * np.sin(twist)
            y_twisted = x_local * np.sin(twist) + y_local * np.cos(twist)
            
            # Convert to cylindrical coordinates
            # Blade wraps around engine axis
            theta_mean = 0  # Reference angle
            theta = theta_mean + y_twisted / r  # Arc length to angle
            
            # Apply lean
            r_leaned = r + section['lean'] * 0.01 * r  # Small lean adjustment
            
            # Convert to Cartesian (engine axis = z)
            x_3d = r_leaned * np.cos(theta)
            y_3d = r_leaned * np.sin(theta)
            z_3d = x_twisted  # Axial direction
            
            section_points = np.column_stack([x_3d, y_3d, z_3d])
            all_points.append(section_points)
            theta_positions.append(theta)
        
        geometry_data = {
            'points': all_points,
            'num_sections': len(sections),
            'num_points_per_section': len(sections[0]['x']),
            'radius_hub': self.stage['radius_hub'],
            'radius_tip': self.stage['radius_tip'],
            'chord': self.stage['chord'],
            'num_blades': self.stage['num_blades']
        }
        
        print(f"  Total points: {len(all_points) * len(all_points[0])}")
        print(f"  Sections: {len(all_points)}")
        
        return geometry_data
    
    def save_geometry(self, output_file: str):
        """Save geometry data to JSON"""
        sections = self.generate_blade_sections()
        geometry_3d = self.create_3d_blade_points(sections)
        
        # Convert numpy arrays to lists for JSON
        geometry_3d['points'] = [pts.tolist() for pts in geometry_3d['points']]
        
        output_data = {
            'metadata': {
                'source': 'turbine_blade_geometry.py',
                'design_file': self.design['metadata']
            },
            'geometry': geometry_3d,
            'sections': sections
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n✓ Geometry saved to: {output_file}")
        
        return geometry_3d

def main():
    """Main execution"""
    print("=" * 70)
    print("TURBINE BLADE GEOMETRY GENERATOR")
    print("=" * 70)
    
    # Load design
    design_file = 'turbine_blade_design.json'
    
    if not os.path.exists(design_file):
        print(f"\nError: Design file '{design_file}' not found!")
        print("Please run turbine_blade_design.py first.")
        return
    
    print(f"\nLoading design from: {design_file}")
    
    generator = TurbineBladeGeometry(design_file)
    
    print(f"\nBlade specifications:")
    print(f"  • Number of blades: {generator.stage['num_blades']}")
    print(f"  • Mean radius: {generator.stage['radius_mean']*1000:.1f} mm")
    print(f"  • Blade height: {generator.stage['blade_height']*1000:.1f} mm")
    print(f"  • Chord: {generator.stage['chord']*1000:.1f} mm")
    
    geometry = generator.save_geometry('turbine_blade_geometry.json')
    
    print("\n" + "=" * 70)
    print("Geometry generation complete!")
    print("Use 'turbine_blade_geometry.json' for mesh generation.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    import os
    main()
