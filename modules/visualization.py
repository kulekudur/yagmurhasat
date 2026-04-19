"""
3D Visualization Module (Enhanced)
Creates interactive 3D visualizations using Plotly
Visualizes realistic building, tank, rain animation, and humanoid workers
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import List, Tuple
import config


class Scene3D:
    """
    Creates and manages 3D scene visualization for the simulation.
    
    Components:
    - Realistic building with multiple levels, windows, and roof
    - Storage tank with dynamic fill level
    - Animated rain particles with intensity-based count
    - Humanoid worker agents (head, body, limbs)
    """
    
    def __init__(self):
        """Initialize the 3D scene."""
        self.fig = None
        self.camera_position = dict(
            x=30, y=30, z=25
        )
        
    def create_realistic_building(self) -> List[go.Mesh3d]:
        """
        Create a realistic building with multiple levels, windows, and roof.
        
        Returns:
            List of Plotly Mesh3d objects representing building components
        """
        building_parts = []
        
        # Main building structure (walls)
        x_walls = [0, config.BUILDING_WIDTH, config.BUILDING_WIDTH, 0,
                   0, config.BUILDING_WIDTH, config.BUILDING_WIDTH, 0]
        y_walls = [0, 0, config.BUILDING_DEPTH, config.BUILDING_DEPTH,
                   0, 0, config.BUILDING_DEPTH, config.BUILDING_DEPTH]
        z_walls = [0, 0, 0, 0,
                   config.BUILDING_HEIGHT, config.BUILDING_HEIGHT, config.BUILDING_HEIGHT, config.BUILDING_HEIGHT]
        
        i_walls = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
        j_walls = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
        k_walls = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
        
        walls = go.Mesh3d(
            x=x_walls, y=y_walls, z=z_walls,
            i=i_walls, j=j_walls, k=k_walls,
            name='Building Walls',
            color='#A9A9A9',
            opacity=0.85,
            showlegend=True
        )
        building_parts.append(walls)
        
        # Roof - triangular pyramid on top
        roof_height = config.BUILDING_HEIGHT
        roof_x = [0, config.BUILDING_WIDTH, config.BUILDING_WIDTH, 0,
                  config.BUILDING_WIDTH / 2]
        roof_y = [0, 0, config.BUILDING_DEPTH, config.BUILDING_DEPTH,
                  config.BUILDING_DEPTH / 2]
        roof_z = [roof_height, roof_height, roof_height, roof_height,
                  roof_height + 3]  # Peak at 3m above walls
        
        roof_i = [0, 1, 2, 3, 0, 1, 2, 3]
        roof_j = [1, 2, 3, 0, 4, 4, 4, 4]
        roof_k = [4, 4, 4, 4, 1, 2, 3, 0]
        
        roof = go.Mesh3d(
            x=roof_x, y=roof_y, z=roof_z,
            i=roof_i, j=roof_j, k=roof_k,
            name='Roof',
            color='#DC143C',
            opacity=0.9,
            showlegend=True
        )
        building_parts.append(roof)
        
        # Add windows as simple rectangular frames
        windows = self._create_windows()
        building_parts.extend(windows)
        
        return building_parts
    
    def _create_windows(self) -> List[go.Scatter3d]:
        """
        Create window representations on building walls.
        
        Returns:
            List of Scatter3d objects representing windows
        """
        windows = []
        window_width = 1.5
        window_height = 1.2
        
        # Front wall windows (y=0)
        for level in range(3):  # 3 levels of windows
            z_pos = 3 + level * 3.5
            for col in range(3):  # 3 columns of windows
                x_pos = 2 + col * 5.5
                
                # Window frame
                x_frame = [x_pos - window_width/2, x_pos + window_width/2, 
                          x_pos + window_width/2, x_pos - window_width/2,
                          x_pos - window_width/2]
                y_frame = [0, 0, 0, 0, 0]
                z_frame = [z_pos - window_height/2, z_pos - window_height/2,
                          z_pos + window_height/2, z_pos + window_height/2,
                          z_pos - window_height/2]
                
                window = go.Scatter3d(
                    x=x_frame, y=y_frame, z=z_frame,
                    mode='lines',
                    line=dict(color='#87CEEB', width=2),
                    name='Windows',
                    showlegend=False
                )
                windows.append(window)
        
        return windows
    
    def create_realistic_tank(self, tank_level_percentage: float = 50) -> go.Surface:
        """
        Create a cylindrical storage tank with dynamic fill level and base.
        
        Args:
            tank_level_percentage: Fill level as percentage (0-100)
            
        Returns:
            Plotly surface object representing tank
        """
        # Position tank next to building
        tank_x_center = config.BUILDING_WIDTH + 8
        tank_y_center = config.BUILDING_DEPTH / 2
        
        # Create cylinder using parametric equations
        theta = np.linspace(0, 2*np.pi, 40)
        z_base = np.linspace(0, config.TANK_HEIGHT, 25)
        
        Theta, Z = np.meshgrid(theta, z_base)
        X = tank_x_center + config.TANK_RADIUS * np.cos(Theta)
        Y = tank_y_center + config.TANK_RADIUS * np.sin(Theta)
        
        # Water fill level calculation
        fill_height = config.TANK_HEIGHT * tank_level_percentage / 100
        
        # Create colormap: water is blue, empty part is gray
        colors = np.ones_like(Z)
        for i in range(Z.shape[0]):
            for j in range(Z.shape[1]):
                if Z[i, j] <= fill_height:
                    colors[i, j] = 0  # Water (blue)
                else:
                    colors[i, j] = 1  # Empty (gray)
        
        tank = go.Surface(
            x=X, y=Y, z=Z,
            surfacecolor=colors,
            colorscale=[[0, '#1E90FF'], [1, '#D3D3D3']],
            name='Tank',
            showlegend=True,
            showscale=False,
            hovertemplate='Tank<extra></extra>'
        )
        
        return tank
    
    def create_tank_base(self) -> go.Mesh3d:
        """
        Create a circular base plate for the tank.
        
        Returns:
            Plotly Mesh3d object for tank base
        """
        tank_x_center = config.BUILDING_WIDTH + 8
        tank_y_center = config.BUILDING_DEPTH / 2
        
        # Create circular base
        theta = np.linspace(0, 2*np.pi, 20)
        x_base = tank_x_center + (config.TANK_RADIUS + 0.2) * np.cos(theta)
        y_base = tank_y_center + (config.TANK_RADIUS + 0.2) * np.sin(theta)
        z_base = np.zeros_like(theta)
        
        # Add center point
        x_base = list(x_base) + [tank_x_center]
        y_base = list(y_base) + [tank_y_center]
        z_base = list(z_base) + [0]
        
        base = go.Scatter3d(
            x=x_base, y=y_base, z=z_base,
            mode='markers',
            marker=dict(size=1, color='#505050'),
            name='Tank Base',
            showlegend=False
        )
        
        return base
    
    def create_animated_rain_particles(
        self,
        rain_intensity: float,
        frame_index: int = 0,
        num_particles: int = None
    ) -> go.Scatter3d:
        """
        Create animated falling rain particles with intensity-based count.
        
        Rain falls from top to bottom, updating position based on frame.
        
        Args:
            rain_intensity: Rain intensity (0-100 mm)
            frame_index: Animation frame number (for falling effect)
            num_particles: Number of particles to render
            
        Returns:
            Plotly Scatter3d object for rain
        """
        if num_particles is None:
            # Scale particle count with rain intensity
            num_particles = int((rain_intensity / 50) * config.RAIN_PARTICLE_COUNT_MAX)
            num_particles = max(0, min(num_particles, config.RAIN_PARTICLE_COUNT_MAX))
        
        if rain_intensity < 0.1 or num_particles == 0:
            # No rain - return empty scatter
            return go.Scatter3d(
                x=[], y=[], z=[],
                mode='markers',
                marker=dict(size=2, color=config.COLOR_RAIN),
                name='Rain',
                showlegend=True,
                hovertemplate='<extra></extra>'
            )
        
        # Create random rain particles with animation effect
        np.random.seed(42)
        base_x = np.random.uniform(-2, config.BUILDING_WIDTH + 5, num_particles)
        base_y = np.random.uniform(-2, config.BUILDING_DEPTH + 2, num_particles)
        
        # Animate rain falling - particles cycle through heights
        fall_speed = 15  # Units per frame
        max_height = config.BUILDING_HEIGHT + 10
        
        # Calculate z position with falling animation
        z = np.zeros_like(base_x)
        for i in range(num_particles):
            # Each particle has different start height
            particle_phase = (frame_index + i) % 100
            z[i] = max_height - (particle_phase * fall_speed / 100) % max_height
        
        # Rain color intensity based on rainfall
        opacity = min(0.8, 0.3 + (rain_intensity / 100) * 0.5)
        
        rain = go.Scatter3d(
            x=base_x, y=base_y, z=z,
            mode='markers',
            marker=dict(
                size=4,
                color=config.COLOR_RAIN,
                opacity=opacity,
                line=dict(width=0)
            ),
            name='Rain',
            showlegend=True,
            hovertemplate='Rain droplet<extra></extra>'
        )
        
        return rain
    
    def create_humanoid_worker(
        self,
        position: Tuple[float, float, float],
        worker_id: int = 0
    ) -> List[go.Scatter3d]:
        """
        Create a humanoid worker model with head, body, and limbs.
        
        Args:
            position: (x, y, z) center position of worker
            worker_id: Worker ID for identification
            
        Returns:
            List of Scatter3d objects representing worker body parts
        """
        x_pos, y_pos, z_pos = position
        worker_parts = []
        
        # Head (sphere-like using scatter)
        head_radius = 0.3
        head_z = z_pos + 1.5
        head = go.Scatter3d(
            x=[x_pos], y=[y_pos], z=[head_z],
            mode='markers',
            marker=dict(
                size=12,
                color='#FFD7A8',  # Skin color
                symbol='circle'
            ),
            name=f'Worker {worker_id}',
            showlegend=False,
            hovertemplate=f'Worker {worker_id}<extra></extra>'
        )
        worker_parts.append(head)
        
        # Body (vertical line from head to waist)
        body_top_z = z_pos + 1.2
        body_bottom_z = z_pos + 0.3
        body = go.Scatter3d(
            x=[x_pos, x_pos],
            y=[y_pos, y_pos],
            z=[body_top_z, body_bottom_z],
            mode='lines',
            line=dict(color='#FF4500', width=6),  # Orange shirt
            name=f'Worker {worker_id} Body',
            showlegend=False,
            hovertemplate='<extra></extra>'
        )
        worker_parts.append(body)
        
        # Left arm
        left_arm_x = [x_pos, x_pos - 0.35]
        left_arm_y = [y_pos, y_pos]
        left_arm_z = [z_pos + 0.9, z_pos + 0.7]
        left_arm = go.Scatter3d(
            x=left_arm_x, y=left_arm_y, z=left_arm_z,
            mode='lines+markers',
            line=dict(color='#FFD7A8', width=4),
            marker=dict(size=5, color='#FFD7A8'),
            showlegend=False,
            hovertemplate='<extra></extra>'
        )
        worker_parts.append(left_arm)
        
        # Right arm
        right_arm_x = [x_pos, x_pos + 0.35]
        right_arm_y = [y_pos, y_pos]
        right_arm_z = [z_pos + 0.9, z_pos + 0.7]
        right_arm = go.Scatter3d(
            x=right_arm_x, y=right_arm_y, z=right_arm_z,
            mode='lines+markers',
            line=dict(color='#FFD7A8', width=4),
            marker=dict(size=5, color='#FFD7A8'),
            showlegend=False,
            hovertemplate='<extra></extra>'
        )
        worker_parts.append(right_arm)
        
        # Left leg
        left_leg_x = [x_pos - 0.15, x_pos - 0.15]
        left_leg_y = [y_pos, y_pos]
        left_leg_z = [z_pos + 0.3, z_pos - 0.3]
        left_leg = go.Scatter3d(
            x=left_leg_x, y=left_leg_y, z=left_leg_z,
            mode='lines+markers',
            line=dict(color='#2F4F4F', width=4),  # Dark pants
            marker=dict(size=5, color='#FFD7A8'),
            showlegend=False,
            hovertemplate='<extra></extra>'
        )
        worker_parts.append(left_leg)
        
        # Right leg
        right_leg_x = [x_pos + 0.15, x_pos + 0.15]
        right_leg_y = [y_pos, y_pos]
        right_leg_z = [z_pos + 0.3, z_pos - 0.3]
        right_leg = go.Scatter3d(
            x=right_leg_x, y=right_leg_y, z=right_leg_z,
            mode='lines+markers',
            line=dict(color='#2F4F4F', width=4),
            marker=dict(size=5, color='#000000'),
            showlegend=False,
            hovertemplate='<extra></extra>'
        )
        worker_parts.append(right_leg)
        
        return worker_parts
    
    def create_workers(
        self,
        worker_positions: List[Tuple[float, float, float]],
        current_hour: int = 12
    ) -> List[go.Scatter3d]:
        """
        Create humanoid worker representations.
        
        Workers are only visible during working hours (9-17).
        
        Args:
            worker_positions: List of (x, y, z) positions
            current_hour: Current hour (0-23)
            
        Returns:
            List of Plotly Scatter3d objects for workers
        """
        workers = []
        
        # Check if it's working hours (9 AM to 5 PM)
        is_working_hours = config.WORK_START_HOUR <= current_hour < config.WORK_END_HOUR
        
        if not worker_positions or not is_working_hours:
            # Return empty workers if not working hours
            return [go.Scatter3d(
                x=[], y=[], z=[],
                mode='markers',
                name='Workers',
                showlegend=True,
                hovertemplate='<extra></extra>'
            )]
        
        for idx, position in enumerate(worker_positions):
            worker_parts = self.create_humanoid_worker(position, worker_id=idx + 1)
            workers.extend(worker_parts)
        
        return workers
    
    def generate_random_worker_positions(
        self,
        num_workers: int
    ) -> List[Tuple[float, float, float]]:
        """
        Generate random positions for workers inside the building.
        
        Args:
            num_workers: Number of workers
            
        Returns:
            List of (x, y, z) positions
        """
        np.random.seed(42)
        positions = []
        for _ in range(num_workers):
            x = np.random.uniform(2, config.BUILDING_WIDTH - 2)
            y = np.random.uniform(2, config.BUILDING_DEPTH - 2)
            z = np.random.uniform(0.5, config.BUILDING_HEIGHT - 1)
            positions.append((x, y, z))
        
        return positions
    
    def create_full_scene(
        self,
        tank_level_percentage: float = 50,
        rain_intensity: float = 0,
        num_workers: int = 10,
        current_hour: int = 12,
        frame_index: int = 0
    ) -> go.Figure:
        """
        Create complete 3D scene with all enhanced components.
        
        Args:
            tank_level_percentage: Tank fill level (0-100)
            rain_intensity: Current rainfall (0-100 mm)
            num_workers: Number of workers to display
            current_hour: Current hour (0-23)
            frame_index: Animation frame for rain
            
        Returns:
            Plotly Figure object
        """
        # Create figure
        self.fig = go.Figure()
        
        # Add realistic building components
        building_parts = self.create_realistic_building()
        for part in building_parts:
            self.fig.add_trace(part)
        
        # Add tank components
        self.fig.add_trace(self.create_realistic_tank(tank_level_percentage))
        self.fig.add_trace(self.create_tank_base())
        
        # Add animated rain
        self.fig.add_trace(self.create_animated_rain_particles(
            rain_intensity, frame_index
        ))
        
        # Add workers (only during working hours)
        worker_positions = self.generate_random_worker_positions(min(num_workers, 20))
        worker_traces = self.create_workers(worker_positions, current_hour)
        for worker_trace in worker_traces:
            self.fig.add_trace(worker_trace)
        
        # Update layout with better camera and scene settings
        self.fig.update_layout(
            title={
                'text': f'Yağmur Hasadı Sistemi - 3D Görünüm (Gün: Dinamik, Saat: {current_hour:02d}:00)',
                'x': 0.5,
                'xanchor': 'center'
            },
            scene=dict(
                xaxis=dict(
                    title='X (meter)',
                    range=[0, config.BUILDING_WIDTH + 12],
                    backgroundcolor='#E0E0E0'
                ),
                yaxis=dict(
                    title='Y (meter)',
                    range=[-2, config.BUILDING_DEPTH + 2],
                    backgroundcolor='#E0E0E0'
                ),
                zaxis=dict(
                    title='Yükseklik (meter)',
                    range=[0, config.BUILDING_HEIGHT + 12],
                    backgroundcolor='#87CEEB'
                ),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.3),
                    center=dict(x=0, y=0, z=0),
                    up=dict(x=0, y=0, z=1)
                ),
                aspectmode='cube',
                bgcolor='#E8F4F8'  # Light cyan background
            ),
            width=1000,
            height=750,
            margin=dict(l=0, r=0, b=0, t=40),
            showlegend=True,
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#000000',
                borderwidth=1
            ),
            hovermode='closest',
            paper_bgcolor='#F5F5F5',
            font=dict(family='Arial', size=11)
        )
        
        return self.fig


class TimeSeriesGraphs:
    """
    Creates 2D time-series visualization graphs with Turkish labels.
    """
    
    @staticmethod
    def create_tank_level_graph(days: List[int], levels: List[float], capacity: float) -> go.Figure:
        """
        Create tank level over time graph with Turkish labels.
        
        Args:
            days: List of day numbers
            levels: List of tank levels
            capacity: Tank capacity for reference
            
        Returns:
            Plotly Figure
        """
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=days,
            y=levels,
            mode='lines',
            name='Depo Seviyesi',
            fill='tozeroy',
            line=dict(color='#1E90FF', width=2),
            fillcolor='rgba(30, 144, 255, 0.3)',
            hovertemplate='Gün: %{x}<br>Seviye: %{y:,.0f} L<extra></extra>'
        ))
        
        # Add capacity line
        fig.add_hline(
            y=capacity,
            line_dash="dash",
            line_color="red",
            annotation_text="Kapasite",
            annotation_position="right"
        )
        
        fig.update_layout(
            title='Zaman İçinde Depo Seviyesi',
            xaxis_title='Gün',
            yaxis_title='Seviye (Litre)',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_rainfall_graph(days: List[int], rainfall: List[float]) -> go.Figure:
        """
        Create daily rainfall visualization with Turkish labels.
        
        Args:
            days: List of day numbers
            rainfall: List of daily rainfall amounts
            
        Returns:
            Plotly Figure
        """
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=days,
            y=rainfall,
            name='Günlük Yağış',
            marker_color='#87CEEB',
            hovertemplate='Gün: %{x}<br>Yağış: %{y:.1f} mm<extra></extra>'
        ))
        
        fig.update_layout(
            title='Günlük Yağış',
            xaxis_title='Gün',
            yaxis_title='Yağış (mm)',
            hovermode='x',
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_consumption_vs_supply_graph(
        days: List[int],
        inflow: List[float],
        outflow: List[float]
    ) -> go.Figure:
        """
        Create consumption vs supply comparison graph with Turkish labels.
        
        Args:
            days: List of day numbers
            inflow: List of collected water amounts
            outflow: List of consumed water amounts
            
        Returns:
            Plotly Figure
        """
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=days,
            y=inflow,
            mode='lines',
            name='Toplanan Su',
            line=dict(color='#32CD32', width=2),
            hovertemplate='Gün: %{x}<br>Toplanan: %{y:,.0f} L<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=days,
            y=outflow,
            mode='lines',
            name='Tüketilen Su',
            line=dict(color='#FF6347', width=2),
            hovertemplate='Gün: %{x}<br>Tüketilen: %{y:,.0f} L<extra></extra>'
        ))
        
        fig.update_layout(
            title='Su Arzı vs Tüketim',
            xaxis_title='Gün',
            yaxis_title='Su (Litre)',
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_monthly_summary_bar(months: List[str], values: List[float], title: str) -> go.Figure:
        """
        Create monthly summary bar chart.
        
        Args:
            months: List of month names
            values: List of values for each month
            title: Chart title (in Turkish)
            
        Returns:
            Plotly Figure
        """
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=months,
            y=values,
            marker_color='#4682B4',
            hovertemplate='%{x}<br>Değer: %{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Ay',
            yaxis_title='Değer',
            template='plotly_white'
        )
        
        return fig
