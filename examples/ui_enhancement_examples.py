"""Example implementations demonstrating UI enhancements.

Shows practical usage of modern UI components, layouts, and effects.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.gui.modern_ui import (
    ModernTheme,
    apply_modern_theme,
    ModernButton,
    ModernLabel,
    StatusBar,
    ProgressIndicator,
    InfoPanel,
    AnimatedTransition,
)
from src.gui.ui_polish import (
    ModernDialog,
    AnimatedLabel,
    NotificationManager,
    ContextMenu,
    MenuBar,
)
from src.gui.layouts import (
    CardPanel,
    TabbedPanel,
    ToolBar,
    GridLayout,
    SidePanel,
    DividerLine,
)
from src.gui.icon_factory import IconFactory


def example_1_themes():
    """Example 1: Using different themes."""
    root = tk.Tk()
    root.title("Theme Examples")
    root.geometry("600x400")
    
    # Create a frame for each theme
    themes = ["light_pro", "dark_pro", "solarized_light", "solarized_dark", "cyberpunk"]
    
    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    for theme_name in themes:
        # Apply theme
        theme = ModernTheme.get_theme(theme_name)
        
        # Create button
        btn = tk.Button(
            frame,
            text=f"Theme: {theme_name}",
            bg=theme.colors["button_bg"],
            fg=theme.colors["button_fg"],
            padx=20,
            pady=10,
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            cursor="hand2",
        )
        btn.pack(pady=5, fill=tk.X)
    
    root.mainloop()


def example_2_modern_components():
    """Example 2: Using modern UI components."""
    root = tk.Tk()
    root.title("Modern Components")
    root.geometry("500x600")
    
    # Apply theme
    theme = ModernTheme.get_theme("dark_pro")
    apply_modern_theme(root, theme)
    
    # Title
    title = ModernLabel(
        root,
        text="Modern UI Components",
        size="large",
        weight="bold",
        fg=theme.colors["fg"],
        bg=theme.colors["bg"],
    )
    title.pack(pady=20)
    
    # Buttons
    button_frame = tk.Frame(root, bg=theme.colors["bg"])
    button_frame.pack(pady=10)
    
    btn1 = ModernButton(
        button_frame,
        text="Primary Button",
        theme=theme,
    )
    btn1.pack(side=tk.LEFT, padx=5)
    
    btn2 = ModernButton(
        button_frame,
        text="Secondary Button",
        theme=theme,
        style="secondary",
    )
    btn2.pack(side=tk.LEFT, padx=5)
    
    # Labels with different sizes
    for size in ["small", "normal", "large", "huge"]:
        label = ModernLabel(
            root,
            text=f"Label size: {size}",
            size=size,
            bg=theme.colors["bg"],
            fg=theme.colors["fg"],
        )
        label.pack(pady=5)
    
    # Status bar
    status = StatusBar(root, theme=theme)
    status.pack(side=tk.BOTTOM, fill=tk.X)
    status.update_generation(150)
    status.update_population(500)
    status.set_status("Running", "success")
    
    # Progress indicator
    spinner = ProgressIndicator(root, size=40, theme=theme)
    spinner.pack(pady=20)
    spinner.start()
    
    root.mainloop()


def example_3_layouts():
    """Example 3: Using layout components."""
    root = tk.Tk()
    root.title("Layouts & Organization")
    root.geometry("700x600")
    
    # Toolbar
    toolbar = ToolBar(root, bg_color="#f5f5f5")
    toolbar.pack(fill=tk.X)
    
    toolbar.add_button("Play", lambda: print("Play"), group="Control")
    toolbar.add_button("Pause", lambda: print("Pause"), group="Control")
    toolbar.add_button("Reset", lambda: print("Reset"), group="Control")
    toolbar.add_separator()
    toolbar.add_button("Save", lambda: print("Save"), group="File")
    toolbar.add_button("Load", lambda: print("Load"), group="File")
    
    # Tabbed interface
    tabs = TabbedPanel(root)
    tabs.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Patterns tab
    patterns_tab = tabs.add_tab("Patterns")
    
    pattern_card = CardPanel(
        patterns_tab,
        title="Saved Patterns",
        shadow=True,
    )
    pattern_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    for i in range(3):
        pattern = tk.Label(
            pattern_card.content_frame,
            text=f"Pattern {i+1}",
            bg="#ffffff",
            font=("Segoe UI", 10),
        )
        pattern.pack(pady=5)
    
    # Statistics tab
    stats_tab = tabs.add_tab("Statistics")
    
    stats_layout = GridLayout(stats_tab, columns=2, padding=10)
    
    for stat in ["Generation", "Population", "Density", "Entropy"]:
        card = CardPanel(stats_tab, title=stat)
        value = tk.Label(
            card.content_frame,
            text="0",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
        )
        value.pack(pady=10)
        stats_layout.add_item(card)
    
    root.mainloop()


def example_4_dialogs_notifications():
    """Example 4: Dialogs and notifications."""
    root = tk.Tk()
    root.title("Dialogs & Notifications")
    root.geometry("400x300")
    
    # Notification manager
    notif_manager = NotificationManager(root)
    
    def show_dialog():
        dialog = ModernDialog(root, title="Export Settings", width=400, height=300)
        
        # Add content
        label = tk.Label(
            dialog.content_frame,
            text="Choose export format:",
            font=("Segoe UI", 11),
        )
        label.pack(pady=10)
        
        formats = ["MP4", "WebM", "PNG Sequence"]
        format_var = tk.StringVar(value="MP4")
        
        for fmt in formats:
            radio = tk.Radiobutton(
                dialog.content_frame,
                text=fmt,
                variable=format_var,
                value=fmt,
            )
            radio.pack(anchor=tk.W, padx=20)
        
        def on_export():
            selected = format_var.get()
            notif_manager.show_notification(
                "Export Started",
                f"Exporting as {selected}...",
                notification_type="info",
            )
            dialog.destroy()
        
        dialog.add_button("Cancel", lambda: dialog.destroy(), style="default")
        dialog.add_button("Export", on_export, style="primary")
    
    def show_success():
        notif_manager.show_notification(
            "Success",
            "Operation completed successfully!",
            notification_type="success",
        )
    
    def show_warning():
        notif_manager.show_notification(
            "Warning",
            "Please check your settings before proceeding.",
            notification_type="warning",
        )
    
    def show_error():
        notif_manager.show_notification(
            "Error",
            "An unexpected error occurred.",
            notification_type="error",
        )
    
    # Buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)
    
    tk.Button(button_frame, text="Show Dialog", command=show_dialog, width=15).pack(pady=5)
    tk.Button(button_frame, text="Success", command=show_success, width=15).pack(pady=5)
    tk.Button(button_frame, text="Warning", command=show_warning, width=15).pack(pady=5)
    tk.Button(button_frame, text="Error", command=show_error, width=15).pack(pady=5)
    
    root.mainloop()


def example_5_icons():
    """Example 5: Icon factory usage."""
    root = tk.Tk()
    root.title("Icon Examples")
    root.geometry("400x500")
    
    # Title
    title = tk.Label(
        root,
        text="Available Icons",
        font=("Segoe UI", 14, "bold"),
    )
    title.pack(pady=10)
    
    # Icon grid
    canvas_frame = tk.Frame(root)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    icons = [
        "play", "pause", "stop", "reset", "save", "load",
        "delete", "settings", "help", "info", "warning", "error",
        "add", "export", "import",
    ]
    
    for i, icon_name in enumerate(icons):
        try:
            # Create frame
            frame = tk.Frame(canvas_frame)
            frame.pack(fill=tk.X, pady=5)
            
            # Icon
            icon_canvas = IconFactory.create_icon(icon_name, size=24, parent=frame)
            icon_canvas.pack(side=tk.LEFT, padx=5)
            
            # Label
            label = tk.Label(frame, text=icon_name, font=("Segoe UI", 10))
            label.pack(side=tk.LEFT)
            
        except Exception as e:
            print(f"Error creating icon {icon_name}: {e}")
    
    root.mainloop()


def example_6_animated_values():
    """Example 6: Animated value displays."""
    root = tk.Tk()
    root.title("Animated Values")
    root.geometry("400x300")
    
    # Title
    title = tk.Label(
        root,
        text="Animated Statistics",
        font=("Segoe UI", 14, "bold"),
    )
    title.pack(pady=20)
    
    # Animated labels
    gen_label = AnimatedLabel(
        root,
        font=("Segoe UI", 24, "bold"),
        fg="#0078d4",
    )
    gen_label.pack(pady=10)
    
    pop_label = AnimatedLabel(
        root,
        font=("Segoe UI", 24, "bold"),
        fg="#107c10",
    )
    pop_label.pack(pady=10)
    
    # Buttons to animate
    def animate_generation():
        gen_label.animate_to(100, duration_ms=1000, prefix="Generation: ")
    
    def animate_population():
        pop_label.animate_to(5000, duration_ms=1500, prefix="Population: ")
    
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)
    
    tk.Button(
        button_frame,
        text="Animate Generation",
        command=animate_generation,
        width=20,
    ).pack(pady=5)
    
    tk.Button(
        button_frame,
        text="Animate Population",
        command=animate_population,
        width=20,
    ).pack(pady=5)
    
    root.mainloop()


def example_7_side_panel():
    """Example 7: Side panel with controls."""
    root = tk.Tk()
    root.title("Side Panel Layout")
    root.geometry("800x600")
    
    # Main layout
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Side panel
    side_panel = SidePanel(main_frame, title="Controls", width=250)
    side_panel.pack(side=tk.LEFT, fill=tk.BOTH)
    
    # Add controls to side panel
    tk.Label(side_panel.content_frame, text="Speed:").pack(pady=5)
    tk.Scale(side_panel.content_frame, from_=1, to=10, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
    
    tk.Label(side_panel.content_frame, text="Zoom:").pack(pady=5)
    tk.Scale(side_panel.content_frame, from_=1, to=5, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
    
    # Main content area
    content = tk.Frame(main_frame)
    content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    canvas = tk.Canvas(content, bg="#ffffff", width=500, height=500)
    canvas.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()


if __name__ == "__main__":
    print("UI Enhancement Examples")
    print("=" * 50)
    print("1. Theme Examples")
    print("2. Modern Components")
    print("3. Layouts & Organization")
    print("4. Dialogs & Notifications")
    print("5. Icons")
    print("6. Animated Values")
    print("7. Side Panel")
    print("=" * 50)
    
    choice = input("Choose example (1-7): ").strip()
    
    examples = {
        "1": example_1_themes,
        "2": example_2_modern_components,
        "3": example_3_layouts,
        "4": example_4_dialogs_notifications,
        "5": example_5_icons,
        "6": example_6_animated_values,
        "7": example_7_side_panel,
    }
    
    if choice in examples:
        examples[choice]()
    else:
        print("Invalid choice!")
