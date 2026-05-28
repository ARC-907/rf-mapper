import tkinter as tk
from tkinter import font as tkfont


class Tooltip:
    """Display a tooltip with a delay when hovering over a widget."""

    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 800) -> None:
        """
        Initialize a tooltip for a widget.

        Args:
            widget: The widget to attach the tooltip to
            text: The tooltip text (can include newlines for multi-line tooltips)
            delay_ms: Delay in milliseconds before showing the tooltip (default: 800ms)
        """
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._id: str | None = None
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)  # Hide on any button press

    def _schedule(self, _event: tk.Event) -> None:
        """Schedule the tooltip to appear after the delay."""
        self._id = self.widget.after(self.delay_ms, self._show)

    def _show(self) -> None:
        """Display the tooltip near the widget."""
        if self._tip is not None:
            return

        # Position the tooltip below and to the right of the widget
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        # Create the tooltip window
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)  # Remove window decorations

        # Create the tooltip label with improved styling
        label = tk.Label(
            self._tip, 
            text=self.text, 
            background="#FFFFDD",  # Light yellow background
            foreground="#000000",  # Black text
            relief="solid", 
            borderwidth=1,
            padx=6,
            pady=4,
            justify=tk.LEFT,
            wraplength=400,  # Wrap text at 400 pixels
            font=tkfont.Font(family="Segoe UI", size=9)
        )
        label.pack()

        # Ensure tooltip stays within screen boundaries
        self._tip.update_idletasks()  # Update to get accurate tooltip dimensions
        tooltip_width = self._tip.winfo_width()
        tooltip_height = self._tip.winfo_height()

        # Get screen dimensions
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()

        # Adjust x position if tooltip would go off right edge of screen
        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 10

        # Adjust y position if tooltip would go off bottom edge of screen
        if y + tooltip_height > screen_height:
            y = self.widget.winfo_rooty() - tooltip_height - 5

        self._tip.wm_geometry(f"+{x}+{y}")

    def _hide(self, _event: tk.Event | None = None) -> None:
        """Hide the tooltip and cancel any pending display."""
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None
