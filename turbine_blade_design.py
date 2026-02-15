"""
Turbine Blade Design Code
=========================

References:
1. Mattingly, J.D., "Elements of Propulsion: Gas Turbines and Rockets", 2nd Ed., AIAA, 2006
2. Mattingly, J.D., Heiser, W.H., Pratt, D.T., "Aircraft Engine Design", 2nd Ed., AIAA, 2002
3. Saravanamuttoo, H.I.H., et al., "Gas Turbine Theory", 6th Ed., Pearson, 2009
4. Aungier, R.H., "Turbine Aerodynamics: Axial-Flow and Radial-Flow Turbine Design and Analysis", ASME Press, 2006

This code implements:
- Engine cycle analysis for turbojet and turbofan engines
- Turbine blade geometry generation based on aerodynamic loading
- Mean-line analysis for turbine stage design
- Output to JSON for downstream geometry and meshing
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import Literal, Dict
import sys

@dataclass
class EngineOperatingConditions:
    """Engine operating point definition"""
    engine_type: Literal['turbojet', 'turbofan']
    altitude: float  # m
    mach_number: float
    thrust_requirement: float  # N
    bypass_ratio: float = 0.0  # 0 for turbojet
    
@dataclass
class CycleParameters:
    """Engine cycle parameters from Mattingly analysis"""
    # Compressor outlet
    T03: float  # K, compressor exit total temp
    P03: float  # Pa, compressor exit total pressure
    
    # Turbine inlet
    T04: float  # K, turbine inlet total temp (TIT)
    P04: float  # Pa, turbine inlet total pressure
    
    # Turbine exit
    T05: float  # K, turbine exit total temp
    P05: float  # Pa, turbine exit total pressure
    
    # Mass flow
    mass_flow: float  # kg/s, core mass flow
    
    # Performance
    pressure_ratio: float
    temperature_ratio: float
    specific_work: float  # J/kg
    
@dataclass
class TurbineStageParameters:
    """Turbine stage design parameters"""
    # Flow angles (deg)
    alpha1: float  # Nozzle exit/rotor inlet flow angle
    alpha2: float  # Rotor exit flow angle
    beta1: float   # Rotor inlet relative flow angle
    beta2: float   # Rotor exit relative flow angle
    
    # Velocities (m/s)
    U: float       # Blade speed
    V1: float      # Nozzle exit absolute velocity
    V2: float      # Rotor exit absolute velocity
    W1: float      # Rotor inlet relative velocity
    W2: float      # Rotor exit relative velocity
    
    # Geometry
    radius_mean: float      # m, mean radius
    radius_tip: float       # m, tip radius
    radius_hub: float       # m, hub radius
    blade_height: float     # m
    chord: float            # m
    pitch: float            # m, blade spacing
    stagger_angle: float    # deg
    
    # Loading
    loading_coefficient: float
    flow_coefficient: float
    degree_of_reaction: float
    
    # Blade count
    num_blades: int

@dataclass
class BladeGeometry:
    """3D blade geometry parameters"""
    # Profile sections (from hub to tip)
    num_sections: int
    sections: list  # List of airfoil sections
    
    # Twist and stacking
    twist_distribution: list  # deg, twist at each section
    lean_angle: list          # deg, lean at each section
    
    # Trailing edge
    trailing_edge_thickness: float  # m
    leading_edge_radius: float      # m

class TurbineBladeDesigner:
    """Main class for turbine blade design"""
    
    def __init__(self, operating_conditions: EngineOperatingConditions):
        self.conditions = operating_conditions
        
        # Constants (Mattingly, Elements of Propulsion, Table 3.1)
        self.gamma = 1.33  # Ratio of specific heats for hot gas
        self.cp = 1148.0   # J/(kg·K), specific heat at constant pressure
        self.R = 287.0     # J/(kg·K), gas constant for air
        
    def calculate_cycle_parameters(self) -> CycleParameters:
        """
        Calculate engine cycle parameters using simplified Brayton cycle
        Reference: Mattingly, Elements of Propulsion, Chapter 3
        """
        # Ambient conditions (ISA atmosphere)
        if self.conditions.altitude <= 11000:
            T_amb = 288.15 - 0.0065 * self.conditions.altitude
            P_amb = 101325 * (T_amb / 288.15) ** 5.256
        else:
            T_amb = 216.65
            P_amb = 22632 * np.exp(-0.0001577 * (self.conditions.altitude - 11000))
        
        # Flight conditions
        T0 = T_amb * (1 + 0.2 * self.conditions.mach_number**2)
        P0 = P_amb * (1 + 0.2 * self.conditions.mach_number**2)**3.5
        
        # Engine assumptions (Mattingly, Aircraft Engine Design, Ch 5)
        if self.conditions.engine_type == 'turbojet':
            OPR = 25.0  # Overall pressure ratio
            TIT = 1650.0  # K, Turbine inlet temperature
            mass_flow = 45.0  # kg/s, estimated
        else:  # turbofan
            OPR = 40.0
            TIT = 1700.0
            mass_flow = 35.0  # kg/s, core flow
        
        # Compressor exit
        eta_c = 0.88  # Compressor efficiency
        pi_c = OPR
        tau_c = pi_c ** ((self.gamma - 1) / self.gamma / eta_c)
        
        T03 = T0 * tau_c
        P03 = P0 * pi_c
        
        # Combustor (Mattingly, Elements of Propulsion, Eq 3.43)
        eta_b = 0.995  # Combustor efficiency
        pi_b = 0.96    # Combustor pressure ratio
        
        T04 = TIT
        P04 = P03 * pi_b
        
        # Turbine (power balance with compressor)
        # Mattingly, Elements of Propulsion, Eq 3.51
        if self.conditions.engine_type == 'turbojet':
            # All turbine power goes to compressor
            work_comp = self.cp * (T03 - T0)
            T05 = T04 - work_comp / self.cp
        else:
            # Account for fan work
            fan_work_ratio = 0.3  # Typical for high bypass
            work_comp = self.cp * (T03 - T0) / (1 - fan_work_ratio)
            T05 = T04 - work_comp / self.cp
        
        eta_t = 0.90  # Turbine efficiency
        tau_t = (T05 / T04)
        pi_t = tau_t ** (self.gamma * eta_t / (self.gamma - 1))
        
        P05 = P04 * pi_t
        
        specific_work = self.cp * (T04 - T05)
        
        return CycleParameters(
            T03=T03, P03=P03,
            T04=T04, P04=P04,
            T05=T05, P05=P05,
            mass_flow=mass_flow,
            pressure_ratio=P04/P05,
            temperature_ratio=T04/T05,
            specific_work=specific_work
        )
    
    def design_turbine_stage(self, cycle: CycleParameters) -> TurbineStageParameters:
        """
        Design turbine stage using mean-line analysis
        Reference: Saravanamuttoo, Gas Turbine Theory, Chapter 7
                   Aungier, Turbine Aerodynamics, Chapter 3
        """
        # Design choices (Aungier, Table 3.1)
        loading_coeff = 2.0  # ψ = ΔH/U², typical range 1.5-2.5
        flow_coeff = 0.6     # φ = Vx/U, typical range 0.4-0.8
        reaction = 0.5       # 50% reaction (Parsons turbine)
        
        # Mean radius selection (Mattingly, Aircraft Engine Design, Eq 10.23)
        U_target = 350.0  # m/s, blade speed at mean
        rpm = 10000  # Assumed rotational speed
        omega = rpm * 2 * np.pi / 60
        
        r_mean = U_target / omega
        
        # Annulus sizing (continuity equation)
        rho_mean = cycle.P04 / (self.R * cycle.T04 * 1.2)  # Account for gas properties
        V_axial = flow_coeff * U_target
        
        A_annulus = cycle.mass_flow / (rho_mean * V_axial)
        blade_height = A_annulus / (2 * np.pi * r_mean)
        
        r_tip = r_mean + blade_height / 2
        r_hub = r_mean - blade_height / 2
        
        # Velocity triangles (Saravanamuttoo, Eq 7.12-7.15)
        delta_h = cycle.specific_work
        U = U_target
        
        # For 50% reaction
        V_theta1 = delta_h / (2 * U) + U / 2
        V_theta2 = -delta_h / (2 * U) + U / 2
        
        V1 = np.sqrt(V_axial**2 + V_theta1**2)
        V2 = np.sqrt(V_axial**2 + V_theta2**2)
        
        alpha1 = np.arctan(V_theta1 / V_axial) * 180 / np.pi
        alpha2 = np.arctan(V_theta2 / V_axial) * 180 / np.pi
        
        W_theta1 = V_theta1 - U
        W_theta2 = V_theta2 - U
        
        W1 = np.sqrt(V_axial**2 + W_theta1**2)
        W2 = np.sqrt(V_axial**2 + W_theta2**2)
        
        beta1 = np.arctan(W_theta1 / V_axial) * 180 / np.pi
        beta2 = np.arctan(W_theta2 / V_axial) * 180 / np.pi
        
        # Blade geometry (Aungier, Section 3.4)
        chord = 0.04  # m, typical for this size
        
        # Zweifel correlation for pitch (Saravanamuttoo, Eq 7.28)
        zweifel_coeff = 0.8
        pitch = chord * np.cos(alpha1 * np.pi / 180) / (2 * zweifel_coeff)
        
        num_blades = int(2 * np.pi * r_mean / pitch)
        pitch = 2 * np.pi * r_mean / num_blades  # Adjust for integer blades
        
        stagger = (alpha1 + alpha2) / 2
        
        return TurbineStageParameters(
            alpha1=alpha1, alpha2=alpha2,
            beta1=beta1, beta2=beta2,
            U=U, V1=V1, V2=V2, W1=W1, W2=W2,
            radius_mean=r_mean,
            radius_tip=r_tip,
            radius_hub=r_hub,
            blade_height=blade_height,
            chord=chord,
            pitch=pitch,
            stagger_angle=stagger,
            loading_coefficient=loading_coeff,
            flow_coefficient=flow_coeff,
            degree_of_reaction=reaction,
            num_blades=num_blades
        )
    
    def generate_blade_geometry(self, stage: TurbineStageParameters) -> BladeGeometry:
        """
        Generate 3D blade geometry with sections
        Reference: Aungier, Turbine Aerodynamics, Chapter 4
        """
        num_sections = 11  # Hub to tip
        
        # Radial distribution (equally spaced)
        radii = np.linspace(stage.radius_hub, stage.radius_tip, num_sections)
        
        sections = []
        twist_dist = []
        lean_dist = []
        
        for i, r in enumerate(radii):
            # Free vortex design (rV_theta = const, Saravanamuttoo Eq 7.44)
            V_theta = stage.V1 * np.sin(stage.alpha1 * np.pi / 180)
            V_theta_section = V_theta * stage.radius_mean / r
            V_axial = stage.V1 * np.cos(stage.alpha1 * np.pi / 180)
            
            alpha_section = np.arctan(V_theta_section / V_axial) * 180 / np.pi
            
            # Blade twist (change in stagger angle)
            twist = alpha_section - stage.alpha1
            twist_dist.append(twist)
            
            # Lean angle (compound lean for stress reduction)
            lean = -2.0 * (r - stage.radius_mean) / stage.blade_height
            lean_dist.append(lean)
            
            # Section parameters
            section = {
                'radius': float(r),
                'chord': float(stage.chord),
                'alpha': float(alpha_section),
                'thickness_to_chord': 0.15 if i < num_sections/2 else 0.10,
                'camber': float(abs(stage.alpha1 - stage.alpha2)),
                'max_thickness_location': 0.35  # x/c
            }
            sections.append(section)
        
        return BladeGeometry(
            num_sections=num_sections,
            sections=sections,
            twist_distribution=twist_dist,
            lean_angle=lean_dist,
            trailing_edge_thickness=0.0008,  # m
            leading_edge_radius=0.002  # m
        )
    
    def save_design_to_json(self, output_file: str):
        """Save complete design to JSON file"""
        print("=" * 70)
        print("TURBINE BLADE DESIGN - DESIGN PROCESS")
        print("=" * 70)
        
        print("\n1. Calculating Engine Cycle Parameters...")
        print(f"   Engine Type: {self.conditions.engine_type.upper()}")
        print(f"   Altitude: {self.conditions.altitude/1000:.1f} km")
        print(f"   Mach Number: {self.conditions.mach_number:.2f}")
        
        cycle = self.calculate_cycle_parameters()
        
        print(f"\n   Cycle Results:")
        print(f"   - Turbine Inlet Temperature (TIT): {cycle.T04:.1f} K")
        print(f"   - Turbine Pressure Ratio: {cycle.pressure_ratio:.2f}")
        print(f"   - Mass Flow Rate: {cycle.mass_flow:.1f} kg/s")
        print(f"   - Specific Work: {cycle.specific_work/1000:.1f} kJ/kg")
        
        print("\n2. Designing Turbine Stage...")
        stage = self.design_turbine_stage(cycle)
        
        print(f"\n   Stage Parameters:")
        print(f"   - Mean Radius: {stage.radius_mean*1000:.1f} mm")
        print(f"   - Blade Height: {stage.blade_height*1000:.1f} mm")
        print(f"   - Blade Speed: {stage.U:.1f} m/s")
        print(f"   - Number of Blades: {stage.num_blades}")
        print(f"   - Flow Coefficient: {stage.flow_coefficient:.3f}")
        print(f"   - Loading Coefficient: {stage.loading_coefficient:.3f}")
        print(f"   - Degree of Reaction: {stage.degree_of_reaction:.2f}")
        
        print("\n3. Generating Blade Geometry...")
        geometry = self.generate_blade_geometry(stage)
        
        print(f"   - Number of Sections: {geometry.num_sections}")
        print(f"   - Chord Length: {stage.chord*1000:.1f} mm")
        print(f"   - Twist Range: {min(geometry.twist_distribution):.1f}° to {max(geometry.twist_distribution):.1f}°")
        
        # Compile output
        output_data = {
            'metadata': {
                'design_code_version': '1.0',
                'references': [
                    'Mattingly, J.D., Elements of Propulsion (2006)',
                    'Mattingly, J.D., Aircraft Engine Design (2002)',
                    'Saravanamuttoo et al., Gas Turbine Theory (2009)',
                    'Aungier, R.H., Turbine Aerodynamics (2006)'
                ]
            },
            'operating_conditions': asdict(self.conditions),
            'cycle_parameters': asdict(cycle),
            'stage_parameters': asdict(stage),
            'blade_geometry': asdict(geometry)
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n✓ Design saved to: {output_file}")
        print("=" * 70)
        
        return output_data

def main():
    """Main execution function"""
    print("\n" + "=" * 70)
    print("TURBINE BLADE DESIGN TOOL")
    print("=" * 70)
    print("\nBased on:")
    print("  • Mattingly - Elements of Propulsion (2006)")
    print("  • Mattingly - Aircraft Engine Design (2002)")
    print("  • Saravanamuttoo - Gas Turbine Theory (2009)")
    print("  • Aungier - Turbine Aerodynamics (2006)")
    print("=" * 70)
    
    # Example: High bypass turbofan
    print("\nDesign Case: High-Bypass Turbofan Engine")
    print("-" * 70)
    
    conditions = EngineOperatingConditions(
        engine_type='turbofan',
        altitude=10668,  # m (35,000 ft cruise)
        mach_number=0.85,
        thrust_requirement=100000,  # N
        bypass_ratio=9.0
    )
    
    designer = TurbineBladeDesigner(conditions)
    output = designer.save_design_to_json('turbine_blade_design.json')
    
    print("\nDesign Summary:")
    print(f"  • {output['stage_parameters']['num_blades']} blades per row")
    print(f"  • Mean diameter: {output['stage_parameters']['radius_mean']*2000:.1f} mm")
    print(f"  • Blade height: {output['stage_parameters']['blade_height']*1000:.1f} mm")
    print(f"  • Turbine inlet temp: {output['cycle_parameters']['T04']:.0f} K")
    
    print("\n" + "=" * 70)
    print("Design complete! Use 'turbine_blade_design.json' for geometry generation.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
