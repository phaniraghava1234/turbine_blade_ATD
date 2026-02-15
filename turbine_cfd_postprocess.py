"""
Turbine Blade CFD Post-Processing
==================================

References:
1. Schroeder, W., Martin, K., Lorensen, B., "The Visualization Toolkit", 
   4th Ed., Kitware, 2006
2. Blazek, J., "Computational Fluid Dynamics", Elsevier, 2015
3. Plotly documentation for scientific visualization

Visualizes CFD simulation results with interactive plots
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import json
import sys
import os

class TurbineCFDPostProcessor:
    """Post-process and visualize turbine blade CFD results"""
    
    def __init__(self, solution_file: str, design_file: str = None):
        """Load solution data"""
        self.solution_file = solution_file
        self.design_file = design_file
        
        # Load solution
        if os.path.exists(solution_file):
            self.load_solution()
        else:
            print(f"Warning: Solution file '{solution_file}' not found!")
            print("Creating synthetic data for demonstration...")
            self.create_synthetic_data()
        
        # Load design parameters if available
        if design_file and os.path.exists(design_file):
            with open(design_file, 'r') as f:
                self.design = json.load(f)
        else:
            self.design = None
    
    def load_solution(self):
        """Load CFD solution from file"""
        print(f"Loading solution from: {self.solution_file}")
        
        # Read data (format: x, y, z, rho, u, v, w, p, T, Mach)
        try:
            data = np.loadtxt(self.solution_file, comments='#')
            
            self.df = pd.DataFrame(data, columns=[
                'x', 'y', 'z', 'rho', 'u', 'v', 'w', 'p', 'T', 'Mach'
            ])
            
            # Compute derived quantities
            self.df['velocity_mag'] = np.sqrt(
                self.df['u']**2 + self.df['v']**2 + self.df['w']**2
            )
            
            # Total pressure
            gamma = 1.4
            self.df['P_total'] = self.df['p'] * (
                1 + 0.5 * (gamma - 1) * self.df['Mach']**2
            ) ** (gamma / (gamma - 1))
            
            # Total temperature
            self.df['T_total'] = self.df['T'] * (
                1 + 0.5 * (gamma - 1) * self.df['Mach']**2
            )
            
            print(f"  Loaded {len(self.df)} points")
            
        except Exception as e:
            print(f"Error loading solution: {e}")
            print("Creating synthetic data instead...")
            self.create_synthetic_data()
    
    def create_synthetic_data(self):
        """Create synthetic CFD data for demonstration"""
        print("Generating synthetic CFD data...")
        
        # Create grid
        x = np.linspace(-0.02, 0.08, 30)
        y = np.linspace(-0.01, 0.01, 20)
        z = np.linspace(0.0, 0.05, 20)
        
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        
        # Flatten
        x_flat = X.flatten()
        y_flat = Y.flatten()
        z_flat = Z.flatten()
        
        # Synthetic flow field (potential flow around cylinder approximation)
        r = np.sqrt(y_flat**2 + z_flat**2)
        theta = np.arctan2(z_flat, y_flat)
        
        # Velocity field
        U_inf = 300.0  # m/s
        R_blade = 0.005  # m
        
        u = U_inf * (1 + (R_blade/r)**2 * (np.cos(2*theta) - 1))
        v = -U_inf * (R_blade/r)**2 * np.sin(2*theta) * np.sin(theta)
        w = U_inf * (R_blade/r)**2 * np.sin(2*theta) * np.cos(theta)
        
        # Handle singularities
        u[r < R_blade] = 0
        v[r < R_blade] = 0
        w[r < R_blade] = 0
        
        # Thermodynamic properties
        P_inf = 2.5e6  # Pa
        T_inf = 1700.0  # K
        gamma = 1.4
        R = 287.0
        
        # Bernoulli approximation
        vel_mag = np.sqrt(u**2 + v**2 + w**2)
        p = P_inf - 0.5 * 1.2 * vel_mag**2  # Approximate
        p = np.maximum(p, 1e5)  # Avoid negative pressure
        
        rho = p / (R * T_inf)
        T = T_inf * np.ones_like(p)
        
        # Mach number
        a = np.sqrt(gamma * R * T)
        mach = vel_mag / a
        
        # Create DataFrame
        self.df = pd.DataFrame({
            'x': x_flat,
            'y': y_flat,
            'z': z_flat,
            'rho': rho,
            'u': u,
            'v': v,
            'w': w,
            'p': p,
            'T': T,
            'Mach': mach,
            'velocity_mag': vel_mag,
            'P_total': p * (1 + 0.5 * (gamma - 1) * mach**2) ** (gamma / (gamma - 1)),
            'T_total': T * (1 + 0.5 * (gamma - 1) * mach**2)
        })
        
        print(f"  Generated {len(self.df)} synthetic data points")
    
    def create_contour_plots(self) -> go.Figure:
        """Create 2D contour plots of key flow variables"""
        print("\nCreating contour plots...")
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Mach Number', 'Total Pressure (MPa)',
                'Temperature (K)', 'Velocity Magnitude (m/s)'
            ),
            specs=[[{'type': 'scatter'}, {'type': 'scatter'}],
                   [{'type': 'scatter'}, {'type': 'scatter'}]]
        )
        
        # Extract mid-span slice (z ~ middle)
        z_mid = (self.df['z'].min() + self.df['z'].max()) / 2
        z_tolerance = (self.df['z'].max() - self.df['z'].min()) / 20
        
        slice_df = self.df[np.abs(self.df['z'] - z_mid) < z_tolerance]
        
        # Mach number
        fig.add_trace(
            go.Scatter(
                x=slice_df['x'],
                y=slice_df['y'],
                mode='markers',
                marker=dict(
                    color=slice_df['Mach'],
                    colorscale='Jet',
                    size=5,
                    colorbar=dict(title='Mach', x=0.45, len=0.4, y=0.75)
                ),
                name='Mach'
            ),
            row=1, col=1
        )
        
        # Total pressure
        fig.add_trace(
            go.Scatter(
                x=slice_df['x'],
                y=slice_df['y'],
                mode='markers',
                marker=dict(
                    color=slice_df['P_total'] / 1e6,  # Convert to MPa
                    colorscale='Plasma',
                    size=5,
                    colorbar=dict(title='MPa', x=1.05, len=0.4, y=0.75)
                ),
                name='P_total'
            ),
            row=1, col=2
        )
        
        # Temperature
        fig.add_trace(
            go.Scatter(
                x=slice_df['x'],
                y=slice_df['y'],
                mode='markers',
                marker=dict(
                    color=slice_df['T'],
                    colorscale='Hot',
                    size=5,
                    colorbar=dict(title='K', x=0.45, len=0.4, y=0.25)
                ),
                name='Temperature'
            ),
            row=2, col=1
        )
        
        # Velocity magnitude
        fig.add_trace(
            go.Scatter(
                x=slice_df['x'],
                y=slice_df['y'],
                mode='markers',
                marker=dict(
                    color=slice_df['velocity_mag'],
                    colorscale='Viridis',
                    size=5,
                    colorbar=dict(title='m/s', x=1.05, len=0.4, y=0.25)
                ),
                name='Velocity'
            ),
            row=2, col=2
        )
        
        # Update axes
        for i in range(1, 3):
            for j in range(1, 3):
                fig.update_xaxes(title_text="x (m)", row=i, col=j)
                fig.update_yaxes(title_text="y (m)", row=i, col=j)
        
        fig.update_layout(
            title_text="Turbine Blade Flow Field - Mid-Span Slice",
            height=800,
            showlegend=False
        )
        
        return fig
    
    def create_3d_visualization(self) -> go.Figure:
        """Create 3D visualization of flow field"""
        print("\nCreating 3D visualization...")
        
        # Sample data for performance
        sample_size = min(2000, len(self.df))
        sample_df = self.df.sample(sample_size)
        
        fig = go.Figure(data=[
            go.Scatter3d(
                x=sample_df['x'],
                y=sample_df['y'],
                z=sample_df['z'],
                mode='markers',
                marker=dict(
                    size=3,
                    color=sample_df['Mach'],
                    colorscale='Jet',
                    colorbar=dict(title='Mach Number'),
                    opacity=0.8
                ),
                text=[f"Mach: {m:.3f}<br>T: {t:.1f} K<br>P: {p/1e6:.2f} MPa" 
                      for m, t, p in zip(sample_df['Mach'], sample_df['T'], sample_df['p'])],
                hoverinfo='text',
                name='Flow Field'
            )
        ])
        
        fig.update_layout(
            title='3D Flow Field Visualization (Colored by Mach Number)',
            scene=dict(
                xaxis_title='X (m)',
                yaxis_title='Y (m)',
                zaxis_title='Z (m)',
                aspectmode='data'
            ),
            width=1000,
            height=800
        )
        
        return fig
    
    def create_performance_plots(self) -> go.Figure:
        """Create performance analysis plots"""
        print("\nCreating performance plots...")
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Mach Number Distribution',
                'Pressure Distribution',
                'Temperature Distribution',
                'Velocity Profile'
            )
        )
        
        # Mach distribution
        fig.add_trace(
            go.Histogram(x=self.df['Mach'], nbinsx=50, name='Mach'),
            row=1, col=1
        )
        
        # Pressure distribution
        fig.add_trace(
            go.Histogram(x=self.df['p']/1e6, nbinsx=50, name='Pressure (MPa)'),
            row=1, col=2
        )
        
        # Temperature distribution
        fig.add_trace(
            go.Histogram(x=self.df['T'], nbinsx=50, name='Temperature (K)'),
            row=2, col=1
        )
        
        # Axial velocity profile
        x_stations = np.linspace(self.df['x'].min(), self.df['x'].max(), 10)
        for x_station in x_stations[::2]:  # Sample stations
            station_data = self.df[np.abs(self.df['x'] - x_station) < 0.005]
            if len(station_data) > 0:
                fig.add_trace(
                    go.Scatter(
                        y=station_data['z'],
                        x=station_data['u'],
                        mode='markers',
                        marker=dict(size=3),
                        name=f'x={x_station:.3f}m',
                        showlegend=True
                    ),
                    row=2, col=2
                )
        
        fig.update_xaxes(title_text="Mach", row=1, col=1)
        fig.update_xaxes(title_text="Pressure (MPa)", row=1, col=2)
        fig.update_xaxes(title_text="Temperature (K)", row=2, col=1)
        fig.update_xaxes(title_text="Axial Velocity (m/s)", row=2, col=2)
        
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=2)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        fig.update_yaxes(title_text="Radial Position (m)", row=2, col=2)
        
        fig.update_layout(
            title_text="Performance Analysis",
            height=800,
            showlegend=True
        )
        
        return fig
    
    def compute_performance_metrics(self) -> dict:
        """Compute key performance metrics"""
        print("\nComputing performance metrics...")
        
        metrics = {}
        
        # Inlet/outlet averages
        x_min, x_max = self.df['x'].min(), self.df['x'].max()
        x_range = x_max - x_min
        
        inlet = self.df[self.df['x'] < x_min + 0.1 * x_range]
        outlet = self.df[self.df['x'] > x_max - 0.1 * x_range]
        
        # Mass-averaged quantities
        if len(inlet) > 0 and len(outlet) > 0:
            metrics['inlet_P_total_avg'] = inlet['P_total'].mean()
            metrics['inlet_T_total_avg'] = inlet['T_total'].mean()
            metrics['outlet_P_total_avg'] = outlet['P_total'].mean()
            metrics['outlet_T_total_avg'] = outlet['T_total'].mean()
            
            # Pressure ratio
            metrics['pressure_ratio'] = (
                metrics['inlet_P_total_avg'] / metrics['outlet_P_total_avg']
            )
            
            # Temperature ratio
            metrics['temperature_ratio'] = (
                metrics['inlet_T_total_avg'] / metrics['outlet_T_total_avg']
            )
            
            # Efficiency (isentropic)
            gamma = 1.4
            T_ratio_isentropic = metrics['pressure_ratio'] ** ((gamma - 1) / gamma)
            metrics['isentropic_efficiency'] = (
                (T_ratio_isentropic - 1) / (metrics['temperature_ratio'] - 1)
            ) if metrics['temperature_ratio'] != 1 else 0.0
        
        # Flow field statistics
        metrics['max_mach'] = float(self.df['Mach'].max())
        metrics['avg_mach'] = float(self.df['Mach'].mean())
        metrics['max_velocity'] = float(self.df['velocity_mag'].max())
        metrics['max_temperature'] = float(self.df['T'].max())
        metrics['min_pressure'] = float(self.df['p'].min())
        
        # Print metrics
        print("\n" + "="*70)
        print("PERFORMANCE METRICS")
        print("="*70)
        for key, value in metrics.items():
            if 'ratio' in key or 'efficiency' in key:
                print(f"  {key}: {value:.4f}")
            elif 'mach' in key.lower() or 'velocity' in key.lower():
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value:.2e}")
        print("="*70)
        
        return metrics
    
    def save_all_visualizations(self, output_dir: str = '.'):
        """Generate and save all visualizations"""
        print("\n" + "="*70)
        print("GENERATING POST-PROCESSING VISUALIZATIONS")
        print("="*70)
        
        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate plots
        contour_fig = self.create_contour_plots()
        viz_3d_fig = self.create_3d_visualization()
        performance_fig = self.create_performance_plots()
        
        # Save HTML files
        contour_file = os.path.join(output_dir, 'cfd_contours.html')
        viz_3d_file = os.path.join(output_dir, 'cfd_3d_visualization.html')
        performance_file = os.path.join(output_dir, 'cfd_performance.html')
        
        contour_fig.write_html(contour_file)
        viz_3d_fig.write_html(viz_3d_file)
        performance_fig.write_html(performance_file)
        
        print(f"\n✓ Contour plots saved: {contour_file}")
        print(f"✓ 3D visualization saved: {viz_3d_file}")
        print(f"✓ Performance plots saved: {performance_file}")
        
        # Compute and save metrics
        metrics = self.compute_performance_metrics()
        metrics_file = os.path.join(output_dir, 'cfd_metrics.json')
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"✓ Metrics saved: {metrics_file}")
        
        print("\n" + "="*70)
        print("POST-PROCESSING COMPLETE")
        print("="*70 + "\n")
        
        return {
            'contours': contour_fig,
            '3d_viz': viz_3d_fig,
            'performance': performance_fig,
            'metrics': metrics
        }

def main():
    """Main execution"""
    print("=" * 70)
    print("TURBINE BLADE CFD POST-PROCESSOR")
    print("=" * 70)
    print("\nVisualization using Plotly for interactive analysis")
    print("=" * 70)
    
    # Files
    solution_file = 'turbine_solution.dat'
    design_file = 'turbine_blade_design.json'
    
    # Create post-processor
    post = TurbineCFDPostProcessor(solution_file, design_file)
    
    # Generate all visualizations
    results = post.save_all_visualizations()
    
    print("\nAll visualizations and metrics saved successfully!")
    print("Open the HTML files in a browser to view interactive plots.")

if __name__ == "__main__":
    main()
