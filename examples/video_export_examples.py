"""
Example: Video Export

This script demonstrates how to create video exports of cellular automaton
simulations using the new video export features.
"""

from pathlib import Path

import numpy as np

from core.simulator import Simulator
from core.config import SimulatorConfig
from export_manager import ExportManager, IMAGEIO_AVAILABLE


def create_glider_video():
    """Create a video of a glider moving across the grid."""
    print("Creating glider video...")
    
    if not IMAGEIO_AVAILABLE:
        print("Error: imageio not available. Install with: pip install imageio imageio-ffmpeg")
        return
    
    # Initialize simulator
    config = SimulatorConfig(width=50, height=50, automaton_mode="Conway's Game of Life")
    sim = Simulator(config)
    sim.initialize(mode="conway", pattern="glider")
    
    # Create export manager
    exporter = ExportManager(theme="light")
    
    # Capture 100 frames
    num_frames = 100
    print(f"Capturing {num_frames} frames...")
    
    for i in range(num_frames):
        grid = sim.get_grid()
        exporter.add_frame(grid)
        sim.step()
        
        if (i + 1) % 10 == 0:
            print(f"  Captured {i + 1}/{num_frames} frames")
    
    # Export as MP4
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "glider_animation.mp4"
    print(f"Exporting to {output_file}...")
    
    success = exporter.export_video(
        str(output_file),
        cell_size=10,
        fps=10,
        codec="mp4"
    )
    
    if success:
        print(f"✓ Video exported successfully to {output_file}")
    else:
        print("✗ Video export failed")


def create_oscillator_comparison():
    """Create a video comparing different oscillators."""
    print("\nCreating oscillator comparison video...")
    
    if not IMAGEIO_AVAILABLE:
        print("Error: imageio not available")
        return
    
    # Create a grid with multiple oscillators
    config = SimulatorConfig(width=80, height=60, automaton_mode="Conway's Game of Life")
    sim = Simulator(config)
    sim.initialize(mode="conway")
    
    # Add oscillators manually
    grid = sim.get_grid()
    
    # Blinker (period 2) at position (10, 10)
    grid[10, 10:13] = 1
    
    # Toad (period 2) at position (20, 10)
    grid[10, 20:23] = 1
    grid[11, 19:22] = 1
    
    # Beacon (period 2) at position (30, 10)
    grid[10:12, 30:32] = 1
    grid[12:14, 32:34] = 1
    
    # Pulsar (period 3) - simplified at position (10, 25)
    # This is a simplified version - real pulsar is larger
    grid[25:28, 10] = 1
    grid[25:28, 16] = 1
    grid[25, 11:16] = 1
    grid[27, 11:16] = 1
    
    exporter = ExportManager(theme="light")
    
    # Capture one full period for each oscillator
    num_frames = 30  # Enough to see all periods
    print(f"Capturing {num_frames} frames...")
    
    for i in range(num_frames):
        exporter.add_frame(sim.get_grid())
        sim.step()
    
    output_file = Path("output") / "oscillators.mp4"
    print(f"Exporting to {output_file}...")
    
    success = exporter.export_video(
        str(output_file),
        cell_size=8,
        fps=5,  # Slower to see oscillations
        codec="mp4"
    )
    
    if success:
        print(f"✓ Video exported successfully to {output_file}")
    else:
        print("✗ Video export failed")


def create_random_soup_video():
    """Create a video of a random soup evolving."""
    print("\nCreating random soup evolution video...")
    
    if not IMAGEIO_AVAILABLE:
        print("Error: imageio not available")
        return
    
    config = SimulatorConfig(width=100, height=100, automaton_mode="Conway's Game of Life")
    sim = Simulator(config)
    sim.initialize(mode="conway", pattern="Random Soup")
    
    exporter = ExportManager(theme="dark")  # Use dark theme for variety
    
    # Capture evolution over 200 frames
    num_frames = 200
    print(f"Capturing {num_frames} frames...")
    
    for i in range(num_frames):
        exporter.add_frame(sim.get_grid())
        sim.step()
        
        if (i + 1) % 20 == 0:
            print(f"  Captured {i + 1}/{num_frames} frames")
    
    output_file = Path("output") / "random_soup.webm"
    print(f"Exporting to {output_file}...")
    
    # Export as WebM for better compression of this longer video
    success = exporter.export_video(
        str(output_file),
        cell_size=4,
        fps=15,
        codec="webm"
    )
    
    if success:
        print(f"✓ Video exported successfully to {output_file}")
        file_size = output_file.stat().st_size / (1024 * 1024)
        print(f"  File size: {file_size:.2f} MB")
    else:
        print("✗ Video export failed")


def create_highlife_replicator():
    """Create a video of HighLife replicator pattern."""
    print("\nCreating HighLife replicator video...")
    
    if not IMAGEIO_AVAILABLE:
        print("Error: imageio not available")
        return
    
    config = SimulatorConfig(width=80, height=80, automaton_mode="High Life")
    sim = Simulator(config)
    sim.initialize(mode="highlife", pattern="Replicator")
    
    exporter = ExportManager(theme="blue")  # Use blue theme
    
    # Capture replication process
    num_frames = 150
    print(f"Capturing {num_frames} frames...")
    
    for i in range(num_frames):
        exporter.add_frame(sim.get_grid())
        sim.step()
        
        if (i + 1) % 15 == 0:
            print(f"  Captured {i + 1}/{num_frames} frames")
    
    output_file = Path("output") / "highlife_replicator.mp4"
    print(f"Exporting to {output_file}...")
    
    success = exporter.export_video(
        str(output_file),
        cell_size=6,
        fps=12,
        codec="mp4"
    )
    
    if success:
        print(f"✓ Video exported successfully to {output_file}")
    else:
        print("✗ Video export failed")


if __name__ == "__main__":
    print("=== LifeGrid Video Export Examples ===\n")
    
    # Check if imageio is available
    if not IMAGEIO_AVAILABLE:
        print("⚠ Warning: imageio package not found!")
        print("Install with: pip install imageio imageio-ffmpeg")
        print("\nSkipping video export examples...\n")
    else:
        print("✓ imageio package found\n")
        
        # Run examples
        create_glider_video()
        create_oscillator_comparison()
        create_random_soup_video()
        create_highlife_replicator()
        
        print("\n=== All videos created successfully! ===")
        print("Check the 'output' directory for generated videos.")
