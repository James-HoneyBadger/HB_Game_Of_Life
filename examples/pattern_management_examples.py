"""
Example: Pattern Favorites and History Management

Demonstrates the new pattern management features including favorites,
history tracking, tagging, and similarity search.
"""

import numpy as np

from core.simulator import Simulator
from core.config import SimulatorConfig
from advanced.pattern_manager import PatternManager, PatternEntry


def demo_basic_favorites():
    """Demonstrate basic favorites functionality."""
    print("=== Basic Favorites Demo ===\n")
    
    # Initialize pattern manager
    pm = PatternManager(data_dir="demo_patterns", max_history=10)
    
    # Create some example patterns
    config = SimulatorConfig(width=20, height=20)
    sim = Simulator(config)
    
    # Pattern 1: Glider
    sim.initialize(mode="conway")
    grid = sim.get_grid()
    grid[5, 5:7] = 1
    grid[6, 6] = 1
    grid[7, 5] = 1
    
    glider_entry = PatternEntry.from_grid(
        name="My Glider",
        mode="conway",
        grid=grid,
        tags=["spaceship", "period-4", "classic"],
        description="Simple glider moving diagonally",
        favorite=True
    )
    
    pm.add_favorite(glider_entry)
    print("✓ Added glider to favorites")
    
    # Pattern 2: Blinker
    sim.initialize(mode="conway")
    grid = sim.get_grid()
    grid[10, 9:12] = 1
    
    blinker_entry = PatternEntry.from_grid(
        name="Blinker",
        mode="conway",
        grid=grid,
        tags=["oscillator", "period-2"],
        description="Period-2 oscillator",
        favorite=True
    )
    
    pm.add_favorite(blinker_entry)
    print("✓ Added blinker to favorites")
    
    # Pattern 3: Block
    sim.initialize(mode="conway")
    grid = sim.get_grid()
    grid[8:10, 8:10] = 1
    
    block_entry = PatternEntry.from_grid(
        name="Block",
        mode="conway",
        grid=grid,
        tags=["still-life", "stable"],
        description="2x2 still life",
        favorite=True
    )
    
    pm.add_favorite(block_entry)
    print("✓ Added block to favorites")
    
    # List favorites
    print(f"\nTotal favorites: {len(pm.get_favorites())}")
    for entry in pm.get_favorites():
        print(f"  - {entry.name} ({', '.join(entry.tags)})")
    
    print()


def demo_history_tracking():
    """Demonstrate pattern history tracking."""
    print("=== History Tracking Demo ===\n")
    
    pm = PatternManager(data_dir="demo_patterns", max_history=5)
    
    # Simulate loading several patterns
    patterns = [
        ("Glider Gun", ["gun", "complex"]),
        ("Pulsar", ["oscillator", "period-3"]),
        ("Lightweight Spaceship", ["spaceship", "period-4"]),
        ("Acorn", ["methuselah", "chaotic"]),
        ("R-Pentomino", ["methuselah", "famous"]),
    ]
    
    config = SimulatorConfig(width=30, height=30)
    sim = Simulator(config)
    
    for name, tags in patterns:
        sim.initialize(mode="conway", pattern="Random Soup")
        grid = sim.get_grid()
        
        entry = PatternEntry.from_grid(
            name=name,
            mode="conway",
            grid=grid,
            tags=tags
        )
        
        pm.add_to_history(entry)
        print(f"✓ Added '{name}' to history")
    
    # Get recent history
    print(f"\nRecent patterns (limited to 5):")
    for i, entry in enumerate(pm.get_history(limit=5), 1):
        print(f"  {i}. {entry.name}")
    
    # Add one more to demonstrate limit
    sim.initialize(mode="conway")
    grid = sim.get_grid()
    grid[10, 10:13] = 1
    
    extra_entry = PatternEntry.from_grid(
        name="Extra Pattern",
        mode="conway",
        grid=grid
    )
    pm.add_to_history(extra_entry)
    
    print(f"\nAfter adding one more (history limited to 5):")
    for i, entry in enumerate(pm.get_history(), 1):
        print(f"  {i}. {entry.name}")
    
    print()


def demo_tag_search():
    """Demonstrate searching patterns by tags."""
    print("=== Tag Search Demo ===\n")
    
    pm = PatternManager(data_dir="demo_patterns")
    
    # Add patterns with various tags
    patterns_data = [
        ("Glider", ["spaceship", "period-4", "small"]),
        ("Lightweight Spaceship", ["spaceship", "period-4", "medium"]),
        ("Middleweight Spaceship", ["spaceship", "period-4", "medium"]),
        ("Blinker", ["oscillator", "period-2", "small"]),
        ("Toad", ["oscillator", "period-2", "small"]),
        ("Beacon", ["oscillator", "period-2", "medium"]),
        ("Pulsar", ["oscillator", "period-3", "large"]),
        ("Block", ["still-life", "small"]),
        ("Beehive", ["still-life", "small"]),
        ("Loaf", ["still-life", "medium"]),
    ]
    
    config = SimulatorConfig(width=20, height=20)
    sim = Simulator(config)
    
    for name, tags in patterns_data:
        sim.initialize(mode="conway")
        grid = sim.get_grid()
        grid[5:8, 5:8] = np.random.randint(0, 2, (3, 3))  # Random pattern
        
        entry = PatternEntry.from_grid(name=name, mode="conway", grid=grid, tags=tags)
        pm.add_to_history(entry)
    
    # Search by different tags
    searches = ["spaceship", "oscillator", "still-life", "period-2", "small"]
    
    for tag in searches:
        results = pm.search_by_tag(tag)
        print(f"Tag '{tag}': {len(results)} patterns")
        for entry in results[:3]:  # Show first 3
            print(f"  - {entry.name}")
        if len(results) > 3:
            print(f"  ... and {len(results) - 3} more")
        print()


def demo_name_search():
    """Demonstrate searching patterns by name."""
    print("=== Name Search Demo ===\n")
    
    pm = PatternManager(data_dir="demo_patterns")
    
    # Search in existing patterns
    searches = ["glider", "ship", "life", "oscillator"]
    
    for query in searches:
        results = pm.search_by_name(query)
        print(f"Query '{query}': {len(results)} results")
        for entry in results[:3]:
            print(f"  - {entry.name}")
        if len(results) > 3:
            print(f"  ... and {len(results) - 3} more")
        print()


def demo_similarity_search():
    """Demonstrate finding similar patterns."""
    print("=== Similarity Search Demo ===\n")
    
    pm = PatternManager(data_dir="demo_patterns")
    
    config = SimulatorConfig(width=20, height=20)
    sim = Simulator(config)
    
    # Create reference pattern (small glider-like)
    sim.initialize(mode="conway")
    grid = sim.get_grid()
    grid[5, 5:7] = 1
    grid[6, 6] = 1
    grid[7, 5] = 1
    
    reference = PatternEntry.from_grid(
        name="Reference Glider",
        mode="conway",
        grid=grid
    )
    
    print(f"Finding patterns similar to '{reference.name}'...")
    print()
    
    # Find similar patterns
    similar = pm.find_similar(reference, threshold=0.3)
    
    if similar:
        print(f"Found {len(similar)} similar patterns:")
        for entry, similarity in similar[:5]:
            print(f"  - {entry.name}: {similarity:.2%} similar")
    else:
        print("No similar patterns found (threshold might be too high)")
    
    print()


def demo_favorites_management():
    """Demonstrate managing favorites."""
    print("=== Favorites Management Demo ===\n")
    
    pm = PatternManager(data_dir="demo_patterns")
    
    # Check if pattern is favorite
    pattern_name = "Glider"
    is_fav = pm.is_favorite(pattern_name)
    print(f"Is '{pattern_name}' a favorite? {is_fav}")
    
    # Remove a favorite
    if is_fav:
        removed = pm.remove_favorite(pattern_name)
        if removed:
            print(f"✓ Removed '{pattern_name}' from favorites")
    
    # List all favorites
    favorites = pm.get_favorites()
    print(f"\nCurrent favorites: {len(favorites)}")
    for entry in favorites:
        print(f"  - {entry.name}")
    
    print()


def demo_pattern_restoration():
    """Demonstrate loading and restoring patterns."""
    print("=== Pattern Restoration Demo ===\n")
    
    pm = PatternManager(data_dir="demo_patterns")
    
    # Get a pattern from favorites
    favorites = pm.get_favorites()
    
    if favorites:
        pattern = favorites[0]
        print(f"Restoring pattern: {pattern.name}")
        print(f"  Mode: {pattern.mode}")
        print(f"  Size: {pattern.width}x{pattern.height}")
        print(f"  Tags: {', '.join(pattern.tags)}")
        print(f"  Description: {pattern.description}")
        
        # Convert back to grid
        grid = pattern.to_grid()
        live_cells = np.sum(grid > 0)
        print(f"  Live cells: {live_cells}")
        
        # Use in a simulation
        config = SimulatorConfig(width=pattern.width, height=pattern.height)
        sim = Simulator(config)
        sim.initialize(mode="conway")
        
        # Set the grid
        automaton = sim.automaton
        if automaton:
            automaton.grid = grid
            print("\n✓ Pattern restored to simulator")
            
            # Run a few steps
            print("\nRunning simulation for 5 generations...")
            for _ in range(5):
                sim.step()
                pop = np.sum(sim.get_grid() > 0)
                print(f"  Generation {sim.generation}: {pop} cells")
    else:
        print("No favorites found to restore")
    
    print()


def demo_complete_workflow():
    """Demonstrate a complete pattern management workflow."""
    print("=== Complete Workflow Demo ===\n")
    
    print("Scenario: Creating and managing a collection of custom patterns\n")
    
    pm = PatternManager(data_dir="demo_patterns")
    config = SimulatorConfig(width=25, height=25)
    sim = Simulator(config)
    
    # 1. Create a custom pattern
    print("1. Creating custom pattern...")
    sim.initialize(mode="conway")
    grid = sim.get_grid()
    
    # Create a custom shape
    grid[10:13, 10:13] = 1
    grid[11, 9] = 1
    grid[11, 13] = 1
    
    custom_pattern = PatternEntry.from_grid(
        name="My Custom Design",
        mode="conway",
        grid=grid,
        tags=["custom", "experiment"],
        description="A custom pattern I created"
    )
    
    pm.add_to_history(custom_pattern)
    print("   ✓ Added to history")
    
    # 2. Test the pattern
    print("\n2. Testing pattern evolution...")
    for i in range(10):
        sim.step()
        if i == 4:
            population = np.sum(sim.get_grid() > 0)
            print(f"   Generation 5: {population} cells")
    
    # 3. Decide to favorite it
    print("\n3. Adding to favorites...")
    custom_pattern.favorite = True
    pm.add_favorite(custom_pattern)
    print("   ✓ Added to favorites")
    
    # 4. Create a variant
    print("\n4. Creating a variant...")
    sim.initialize(mode="conway")
    grid = sim.get_grid()
    grid[10:13, 10:13] = 1
    grid[11, 9] = 1
    grid[11, 13] = 1
    grid[12, 14] = 1  # Small change
    
    variant_pattern = PatternEntry.from_grid(
        name="My Custom Design v2",
        mode="conway",
        grid=grid,
        tags=["custom", "experiment", "variant"],
        description="Variant of my custom pattern"
    )
    
    pm.add_to_history(variant_pattern)
    print("   ✓ Added variant to history")
    
    # 5. Find similar patterns
    print("\n5. Finding similar patterns...")
    similar = pm.find_similar(custom_pattern, threshold=0.5)
    print(f"   Found {len(similar)} similar pattern(s):")
    for entry, similarity in similar:
        print(f"   - {entry.name}: {similarity:.1%} similar")
    
    # 6. Organize with tags
    print("\n6. Searching by tags...")
    custom_patterns = pm.search_by_tag("custom")
    print(f"   Found {len(custom_patterns)} pattern(s) with 'custom' tag")
    
    # 7. Final summary
    print("\n7. Summary:")
    print(f"   Total favorites: {len(pm.get_favorites())}")
    print(f"   Total history entries: {len(pm.get_history())}")
    
    print("\n✓ Workflow complete!")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LIFEGRID PATTERN MANAGEMENT EXAMPLES")
    print("=" * 60 + "\n")
    
    demo_basic_favorites()
    demo_history_tracking()
    demo_tag_search()
    demo_name_search()
    demo_similarity_search()
    demo_favorites_management()
    demo_pattern_restoration()
    demo_complete_workflow()
    
    print("=" * 60)
    print("All pattern management examples completed!")
    print("\nNote: Demo patterns are saved in 'demo_patterns' directory")
    print("=" * 60)
