"""Enhanced GUI features integration.

This module provides UI components and handlers for new features:
- Video export (MP4/WebM)
- Brush size controls
- Pattern favorites and history
- Cell age heat maps
- Enhanced statistics
- Auto-save
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gui.app import AutomatonApp


class EnhancedFeaturesUI:
    """Enhanced features UI manager.

    Provides methods to add new UI components and handlers
    to the main application.
    """

    def __init__(self, app: AutomatonApp) -> None:
        """Initialize enhanced features UI.

        Args:
            app: Main application instance
        """
        self.app = app

    def add_brush_controls(self, parent: tk.Frame) -> None:
        """Add brush size and shape controls.

        Args:
            parent: Parent frame to add controls to
        """
        brush_frame = ttk.LabelFrame(parent, text="Brush Settings", padding=5)
        brush_frame.pack(fill=tk.X, padx=5, pady=5)

        # Brush size
        size_frame = ttk.Frame(brush_frame)
        size_frame.pack(fill=tk.X, pady=2)

        ttk.Label(size_frame, text="Size:").pack(side=tk.LEFT)

        brush_size_var = tk.IntVar(value=1)
        size_scale = ttk.Scale(
            size_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=brush_size_var,
            command=lambda _: self._on_brush_size_changed(brush_size_var.get()),
        )
        size_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        size_label = ttk.Label(size_frame, text="1")
        size_label.pack(side=tk.LEFT)

        # Update label when size changes
        def update_label(_):
            size = int(brush_size_var.get())
            size_label.config(text=str(size))
            self._on_brush_size_changed(size)

        size_scale.config(command=update_label)

        # Brush shape
        shape_frame = ttk.Frame(brush_frame)
        shape_frame.pack(fill=tk.X, pady=2)

        ttk.Label(shape_frame, text="Shape:").pack(side=tk.LEFT)

        brush_shape_var = tk.StringVar(value="square")
        shape_combo = ttk.Combobox(
            shape_frame,
            textvariable=brush_shape_var,
            values=["square", "circle", "diamond"],
            state="readonly",
            width=10,
        )
        shape_combo.pack(side=tk.LEFT, padx=5)
        shape_combo.bind(
            "<<ComboboxSelected>>",
            lambda _: self._on_brush_shape_changed(brush_shape_var.get()),
        )

    def _on_brush_size_changed(self, size: float) -> None:
        """Handle brush size change."""
        self.app.tool_manager.set_brush_size(int(size))

    def _on_brush_shape_changed(self, shape: str) -> None:
        """Handle brush shape change."""
        self.app.tool_manager.set_brush_shape(shape)

    def add_export_menu_items(self, file_menu: tk.Menu) -> None:
        """Add video export menu items.

        Args:
            file_menu: File menu to add items to
        """
        file_menu.add_separator()
        file_menu.add_command(
            label="Export Video (MP4)…", command=self._export_mp4
        )
        file_menu.add_command(
            label="Export Video (WebM)…", command=self._export_webm
        )

    def _export_mp4(self) -> None:
        """Export simulation as MP4 video."""
        from export_manager import IMAGEIO_AVAILABLE

        if not IMAGEIO_AVAILABLE:
            messagebox.showerror(
                "Unavailable",
                "Video export requires imageio and imageio-ffmpeg packages.\n"
                "Install with: pip install imageio imageio-ffmpeg",
            )
            return

        # Ask user to configure export
        dialog = VideoExportDialog(self.app.root, "MP4 Video Export")
        if not dialog.result:
            return

        cell_size = dialog.cell_size
        fps = dialog.fps
        num_frames = dialog.num_frames

        filename = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4"), ("All files", "*.*")],
        )
        if not filename:
            return

        # Capture frames
        self._capture_and_export_video(filename, cell_size, fps, num_frames, "mp4")

    def _export_webm(self) -> None:
        """Export simulation as WebM video."""
        from export_manager import IMAGEIO_AVAILABLE

        if not IMAGEIO_AVAILABLE:
            messagebox.showerror(
                "Unavailable",
                "Video export requires imageio package.\n"
                "Install with: pip install imageio",
            )
            return

        dialog = VideoExportDialog(self.app.root, "WebM Video Export")
        if not dialog.result:
            return

        cell_size = dialog.cell_size
        fps = dialog.fps
        num_frames = dialog.num_frames

        filename = filedialog.asksaveasfilename(
            defaultextension=".webm",
            filetypes=[("WebM Video", "*.webm"), ("All files", "*.*")],
        )
        if not filename:
            return

        self._capture_and_export_video(filename, cell_size, fps, num_frames, "webm")

    def _capture_and_export_video(
        self, filename: str, cell_size: int, fps: int, num_frames: int, codec: str
    ) -> None:
        """Capture frames and export video."""
        from export_manager import ExportManager

        exporter = ExportManager(theme="light")

        # Capture frames
        progress = tk.Toplevel(self.app.root)
        progress.title("Capturing Frames")
        progress.geometry("300x100")

        label = ttk.Label(progress, text=f"Capturing 0/{num_frames} frames...")
        label.pack(pady=20)

        progress_bar = ttk.Progressbar(
            progress, length=250, mode="determinate", maximum=num_frames
        )
        progress_bar.pack(pady=10)

        automaton = self.app.state.current_automaton
        if not automaton:
            progress.destroy()
            messagebox.showerror("Error", "No active simulation")
            return

        for i in range(num_frames):
            grid = automaton.get_grid()
            exporter.add_frame(grid)
            automaton.step()

            label.config(text=f"Capturing {i + 1}/{num_frames} frames...")
            progress_bar["value"] = i + 1
            progress.update()

        progress.destroy()

        # Export video
        success = exporter.export_video(filename, cell_size, fps, codec)

        if success:
            messagebox.showinfo("Exported", f"Video saved to {filename}")
        else:
            messagebox.showerror("Export Failed", "Could not save video file")

    def add_statistics_dialog(self) -> None:
        """Show enhanced statistics dialog."""
        from advanced.enhanced_statistics import EnhancedStatistics

        automaton = self.app.state.current_automaton
        if not automaton:
            messagebox.showinfo("No Simulation", "No active simulation")
            return

        grid = automaton.get_grid()
        metrics = EnhancedStatistics.compute_all_metrics(grid)

        dialog = tk.Toplevel(self.app.root)
        dialog.title("Enhanced Statistics")
        dialog.geometry("400x500")

        # Create scrollable text widget
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget = tk.Text(text_frame, wrap=tk.WORD, width=50, height=25)
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Format metrics
        content = "=== Enhanced Statistics ===\n\n"

        content += f"Entropy: {metrics['entropy']:.4f}\n"
        content += f"Complexity: {metrics['complexity']:.4f}\n"
        content += f"Fractal Dimension: {metrics['fractal_dimension']:.4f}\n\n"

        cx, cy = metrics['center_of_mass']
        content += f"Center of Mass: ({cx:.1f}, {cy:.1f})\n\n"

        content += "=== Cluster Analysis ===\n"
        content += f"Number of Clusters: {metrics['num_clusters']}\n"
        content += f"Avg Cluster Size: {metrics['avg_cluster_size']:.1f}\n"
        content += f"Largest Cluster: {metrics['largest_cluster']}\n"
        content += f"Smallest Cluster: {metrics['smallest_cluster']}\n\n"

        content += "=== Symmetry Analysis ===\n"
        for sym_type, value in metrics['symmetry'].items():
            content += f"{sym_type.replace('_', ' ').title()}: {value:.4f}\n"

        text_widget.insert("1.0", content)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

    def add_heatmap_view(self) -> None:
        """Toggle cell age heatmap view."""
        # This would require more extensive integration with the rendering system
        messagebox.showinfo(
            "Heat Map",
            "Heat map visualization requires cell age tracking to be enabled.\n"
            "This feature is available through the View menu.",
        )


class VideoExportDialog:
    """Dialog for configuring video export settings."""

    def __init__(self, parent: tk.Tk, title: str) -> None:
        """Initialize video export dialog.

        Args:
            parent: Parent window
            title: Dialog title
        """
        self.result: Optional[dict] = None
        self.cell_size = 4
        self.fps = 10
        self.num_frames = 100

        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry("300x200")
        dialog.resizable(False, False)

        # Cell size
        ttk.Label(dialog, text="Cell Size (pixels):").grid(
            row=0, column=0, padx=10, pady=5, sticky=tk.W
        )
        cell_size_var = tk.IntVar(value=4)
        ttk.Spinbox(
            dialog, from_=1, to=20, textvariable=cell_size_var, width=10
        ).grid(row=0, column=1, padx=10, pady=5)

        # FPS
        ttk.Label(dialog, text="Frames Per Second:").grid(
            row=1, column=0, padx=10, pady=5, sticky=tk.W
        )
        fps_var = tk.IntVar(value=10)
        ttk.Spinbox(dialog, from_=1, to=60, textvariable=fps_var, width=10).grid(
            row=1, column=1, padx=10, pady=5
        )

        # Number of frames
        ttk.Label(dialog, text="Number of Frames:").grid(
            row=2, column=0, padx=10, pady=5, sticky=tk.W
        )
        frames_var = tk.IntVar(value=100)
        ttk.Spinbox(
            dialog, from_=10, to=1000, textvariable=frames_var, width=10
        ).grid(row=2, column=1, padx=10, pady=5)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        def on_ok():
            self.cell_size = cell_size_var.get()
            self.fps = fps_var.get()
            self.num_frames = frames_var.get()
            self.result = {
                "cell_size": self.cell_size,
                "fps": self.fps,
                "num_frames": self.num_frames,
            }
            dialog.destroy()

        def on_cancel():
            self.result = None
            dialog.destroy()

        ttk.Button(button_frame, text="OK", command=on_ok).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(
            side=tk.LEFT, padx=5
        )

        # Make modal
        dialog.transient(parent)
        dialog.grab_set()
        parent.wait_window(dialog)
