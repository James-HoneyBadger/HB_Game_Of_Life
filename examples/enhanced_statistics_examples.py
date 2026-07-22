"""
Example: Enhanced Statistics and Analysis

Demonstrates the new enhanced statistics features including entropy,
complexity, fractal dimension, and cluster analysis.
"""

import numpy as np

from core.simulator import Simulator
from core.config import SimulatorConfig
from advanced.enhanced_statistics import EnhancedStatistics


def analyze_still_life():
    """Analyze a simple still life pattern (Block)."""
    print("=== Analyzing Still Life (Block) ===\n")
    
    # Create a 2x2 block
    grid = np.zeros((20, 20), dtype=int)
    grid[9:11, 9:11] = 1
    
    metrics = EnhancedStatistics.compute_all_metrics(grid)
    
    print(f"Entropy: {metrics['entropy']:.4f}")
    print(f"Complexity: {metrics['complexity']:.4f}")
    print(f"Fractal Dimension: {metrics['fractal_dimension']:.4f}")
    print(f"Number of Clusters: {metrics['num_clusters']}")
    print(f"Center of Mass: ({metrics['center_of_mass'][0]:.1f}, {metrics['center_of_mass'][1]:.1f})")
    
    print("\nSymmetry Analysis:")
    for sym_type, value in metrics['symmetry'].items():
        print(f"  {sym_type.replace('_', ' ').title()}: {value:.4f}")
    
    print("\nExpected: Low entropy, low complexity, perfect symmetries")
    print()


def analyze_oscillator():
    """Analyze an oscillator pattern over its period."""
    print("=== Analyzing Oscillator (Blinker) ===\n")
    
    config = SimulatorConfig(width=20, height=20, automaton_mode="Conway's Game of Life")
    sim = Simulator(config)
    sim.initialize(mode="conway")
    
    # Create blinker
    grid = sim.get_grid()
    grid[9, 9:12] = 1
    
    print("State 1 (Horizontal):")
    metrics1 = EnhancedStatistics.compute_all_metrics(grid)
    print(f"  Entropy: {metrics1['entropy']:.4f}")
    print(f"  Horizontal Symmetry: {metrics1['symmetry']['horizontal']:.4f}")
    print(f"  Vertical Symmetry: {metrics1['symmetry']['vertical']:.4f}")
    
    # Step once
    sim.step()
    grid = sim.get_grid()
    
    print("\nState 2 (Vertical):")
    metrics2 = EnhancedStatistics.compute_all_metrics(grid)
    print(f"  Entropy: {metrics2['entropy']:.4f}")
    print(f"  Horizontal Symmetry: {metrics2['symmetry']['horizontal']:.4f}")
    print(f"  Vertical Symmetry: {metrics2['symmetry']['vertical']:.4f}")
    
    print("\nNote: Symmetry values flip between states")
    print()


def analyze_random_soup():
    """Analyze a random soup as it evolves."""
    print("=== Analyzing Random Soup Evolution ===\n")
    
    config = SimulatorConfig(width=50, height=50, automaton_mode="Conway's Game of Life")
    sim = Simulator(config)
    sim.initialize(mode="conway", pattern="Random Soup")
    
    print("Generation | Entropy | Complexity | Clusters | Population")
    print("-" * 60)
    
    previous_grid = None
    for gen in [0, 10, 50, 100, 200]:
        # Step to desired generation
        while sim.generation < gen:
            previous_grid = sim.get_grid().copy()
            sim.step()
        
        grid = sim.get_grid()
        metrics = EnhancedStatistics.compute_all_metrics(grid, previous_grid)
        population = np.sum(grid > 0)
        
        print(f"{gen:10d} | {metrics['entropy']:7.4f} | "
              f"{metrics['complexity']:10.4f} | "
              f"{metrics['num_clusters']:8d} | {population:10d}")
    
    print("\nObservation: Entropy and complexity typically decrease as pattern stabilizes")
    print()


def analyze_fractal_patterns():
    """Compare fractal dimensions of different patterns."""
    print("=== Fractal Dimension Analysis ===\n")
    
    patterns = {
        "Single Cell": np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]]),
        "Line": np.array([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]),
        "Filled Square": np.ones((10, 10)),
    }
    
    # Create more interesting patterns
    # Sierpinski-like pattern
    sierpinski = np.zeros((16, 16), dtype=int)
    sierpinski[0, 0] = 1
    for _ in range(4):
        size = sierpinski.shape[0]
        expanded = np.zeros((size * 2, size * 2), dtype=int)
        expanded[0:size, 0:size] = sierpinski
        expanded[0:size, size:] = sierpinski
        expanded[size:, 0:size] = sierpinski
        sierpinski = expanded
    
    patterns["Sierpinski-like"] = sierpinski[:16, :16]
    
    # Random scattered points
    random_pattern = np.zeros((20, 20), dtype=int)
    np.random.seed(42)
    coords = np.random.randint(0, 20, size=(30, 2))
    for y, x in coords:
        random_pattern[y, x] = 1
    patterns["Random Scatter"] = random_pattern
    
    print("Pattern            | Fractal Dimension")
    print("-" * 40)
    
    for name, grid in patterns.items():
        # Pad smaller grids to minimum size
        if grid.shape[0] < 16 or grid.shape[1] < 16:
            padded = np.zeros((max(16, grid.shape[0]), max(16, grid.shape[1])), dtype=int)
            padded[:grid.shape[0], :grid.shape[1]] = grid
            grid = padded
        
        dim = EnhancedStatistics.box_counting_dimension(grid)
        print(f"{name:18s} | {dim:17.4f}")
    
    print("\nNote: Higher dimension = more space-filling pattern")
    print()


def analyze_cluster_evolution():
    """Track cluster formation and evolution."""
    print("=== Cluster Evolution Analysis ===\n")
    
    config = SimulatorConfig(width=60, height=60, automaton_mode="Conway's Game of Life")
    sim = Simulator(config)
    
    # Create multiple separated gliders
    grid = sim.get_grid()
    
    # Glider 1
    grid[10, 10:12] = 1
    grid[11, 11] = 1
    grid[12, 10] = 1
    
    # Glider 2
    grid[10, 30:32] = 1
    grid[11, 31] = 1
    grid[12, 30] = 1
    
    # Glider 3
    grid[30, 10:12] = 1
    grid[31, 11] = 1
    grid[32, 10] = 1
    
    # Some random noise
    np.random.seed(42)
    noise_mask = np.random.random(grid.shape) < 0.02
    grid[noise_mask] = 1
    
    print("Generation | Clusters | Avg Size | Largest | Smallest")
    print("-" * 55)
    
    for _ in range(5):
        metrics = EnhancedStatistics.cluster_statistics(sim.get_grid())
        print(f"{sim.generation:10d} | {metrics['num_clusters']:8d} | "
              f"{metrics['avg_cluster_size']:8.2f} | "
              f"{metrics['largest_cluster']:7d} | "
              f"{metrics['smallest_cluster']:8d}")
        
        # Step simulation forward
        for _ in range(10):
            sim.step()
    
    print("\nObservation: Clusters merge, split, or disappear as simulation progresses")
    print()


def analyze_symmetry_preservation():
    """Check how well patterns preserve symmetry over time."""
    print("=== Symmetry Preservation Analysis ===\n")
    
    config = SimulatorConfig(width=40, height=40, automaton_mode="Conway's Game of Life")
    sim = Simulator(config)
    sim.initialize(mode="conway")
    
    # Create perfectly symmetric pattern (4-fold)
    grid = sim.get_grid()
    center = grid.shape[0] // 2
    
    # Create pattern in one quadrant
    grid[center - 2, center + 1] = 1
    grid[center - 1, center + 1:center + 3] = 1
    grid[center, center + 2] = 1
    
    # Mirror to other quadrants
    grid[center - 2, center - 2] = 1
    grid[center - 1, center - 3:center - 1] = 1
    grid[center, center - 3] = 1
    
    grid[center + 1, center + 1] = 1
    grid[center + 2, center + 1:center + 3] = 1
    grid[center + 3, center + 2] = 1
    
    grid[center + 1, center - 2] = 1
    grid[center + 2, center - 3:center - 1] = 1
    grid[center + 3, center - 3] = 1
    
    print("Generation | H-Sym | V-Sym | R-Sym | D-Sym")
    print("-" * 50)
    
    for gen in range(0, 21, 5):
        while sim.generation < gen:
            sim.step()
        
        metrics = EnhancedStatistics.compute_all_metrics(sim.get_grid())
        sym = metrics['symmetry']
        
        print(f"{gen:10d} | {sym['horizontal']:.3f} | "
              f"{sym['vertical']:.3f} | "
              f"{sym['rotational_180']:.3f} | "
              f"{sym['diagonal']:.3f}")
    
    print("\nNote: Perfect symmetry = 1.000, No symmetry = ~0.5-0.6")
    print()


def comprehensive_pattern_report():
    """Generate a comprehensive analysis report for a pattern."""
    print("=== Comprehensive Pattern Analysis ===\n")
    
    config = SimulatorConfig(width=50, height=50, automaton_mode="Conway's Game of Life")
    sim = Simulator(config)
    sim.initialize(mode="conway", pattern="R-Pentomino")
    
    # Let it evolve a bit
    for _ in range(50):
        sim.step()
    
    grid = sim.get_grid()
    metrics = EnhancedStatistics.compute_all_metrics(grid)
    
    print("PATTERN: R-Pentomino (Generation 50)")
    print("=" * 50)
    
    print("\n1. Basic Information")
    print(f"   Population: {np.sum(grid > 0)}")
    print(f"   Density: {np.sum(grid > 0) / grid.size:.4f}")
    
    print("\n2. Information Theory")
    print(f"   Entropy: {metrics['entropy']:.4f}")
    print(f"   Complexity Score: {metrics['complexity']:.4f}")
    
    print("\n3. Geometric Properties")
    cx, cy = metrics['center_of_mass']
    print(f"   Center of Mass: ({cx:.2f}, {cy:.2f})")
    print(f"   Fractal Dimension: {metrics['fractal_dimension']:.4f}")
    
    print("\n4. Cluster Analysis")
    print(f"   Number of Clusters: {metrics['num_clusters']}")
    print(f"   Average Cluster Size: {metrics['avg_cluster_size']:.2f}")
    print(f"   Largest Cluster: {metrics['largest_cluster']}")
    print(f"   Smallest Cluster: {metrics['smallest_cluster']}")
    
    print("\n5. Symmetry Analysis")
    for sym_type, value in metrics['symmetry'].items():
        print(f"   {sym_type.replace('_', ' ').title()}: {value:.4f}")
    
    print("\n" + "=" * 50)
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LIFEGRID ENHANCED STATISTICS EXAMPLES")
    print("=" * 60 + "\n")
    
    analyze_still_life()
    analyze_oscillator()
    analyze_random_soup()
    analyze_fractal_patterns()
    analyze_cluster_evolution()
    analyze_symmetry_preservation()
    comprehensive_pattern_report()
    
    print("=" * 60)
    print("All analysis examples completed!")
    print("=" * 60)
