"""
Base View for the RF Analyzer GUI.

This module contains the BaseView class, which provides common functionality
for all view classes in the RF Analyzer GUI.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional, Any

from sim_rf_map.ui.lang import STRINGS
from sim_rf_map.tooltip import Tooltip

class BaseView:
    """
    Base class for all view components.
    
    This class provides common functionality for all view classes,
    such as creating buttons, labels, and tooltips.
    """
    
    def __init__(self, parent: tk.Widget, lang: str = "en") -> None:
        """
        Initialize the base view.
        
        Args:
            parent: The parent widget
            lang: The language code
        """
        self.parent = parent
        self.lang = lang
        self.tooltips: list[Tooltip] = []
        
    def get_str(self, key: str) -> str:
        """
        Get a localized string.
        
        Args:
            key: The string key
            
        Returns:
            The localized string
        """
        return STRINGS.get(self.lang, {}).get(key, key)
        
    def make_button(self, label: str, command: Callable, tooltip: str,
                   icon_name: Optional[str] = None, enabled: bool = True) -> ttk.Button:
        """
        Create a button with a tooltip.
        
        Args:
            label: The button label
            command: The button command
            tooltip: The tooltip text
            icon_name: Optional icon name
            enabled: Whether the button is enabled
            
        Returns:
            The created button
        """
        button = ttk.Button(self.parent, text=label, command=command)
        
        if not enabled:
            button.state(["disabled"])
            
        if icon_name:
            from sim_rf_map.ui.icons import get_icon_text
            icon_text = get_icon_text(icon_name)
            if icon_text:
                button.configure(text=f"{icon_text} {label}")
                
        self.tooltips.append(Tooltip(button, tooltip))
        
        return button
        
    def make_label(self, text: str, tooltip: Optional[str] = None) -> ttk.Label:
        """
        Create a label with an optional tooltip.
        
        Args:
            text: The label text
            tooltip: Optional tooltip text
            
        Returns:
            The created label
        """
        label = ttk.Label(self.parent, text=text)
        
        if tooltip:
            self.tooltips.append(Tooltip(label, tooltip))
            
        return label
        
    def make_combobox(self, values: list[str], default: str,
                     tooltip: Optional[str] = None) -> ttk.Combobox:
        """
        Create a combobox with an optional tooltip.
        
        Args:
            values: The combobox values
            default: The default value
            tooltip: Optional tooltip text
            
        Returns:
            The created combobox
        """
        combobox = ttk.Combobox(self.parent, values=values, state="readonly")
        combobox.set(default)
        
        if tooltip:
            self.tooltips.append(Tooltip(combobox, tooltip))
            
        return combobox
        
    def make_entry(self, default: str, width: int = 10,
                  tooltip: Optional[str] = None) -> ttk.Entry:
        """
        Create an entry with an optional tooltip.
        
        Args:
            default: The default value
            width: The entry width
            tooltip: Optional tooltip text
            
        Returns:
            The created entry
        """
        entry = ttk.Entry(self.parent, width=width)
        entry.insert(0, default)
        
        if tooltip:
            self.tooltips.append(Tooltip(entry, tooltip))
            
        return entry
        
    def make_checkbox(self, text: str, variable: tk.BooleanVar,
                     tooltip: Optional[str] = None) -> ttk.Checkbutton:
        """
        Create a checkbox with an optional tooltip.
        
        Args:
            text: The checkbox text
            variable: The variable to bind to
            tooltip: Optional tooltip text
            
        Returns:
            The created checkbox
        """
        checkbox = ttk.Checkbutton(self.parent, text=text, variable=variable)
        
        if tooltip:
            self.tooltips.append(Tooltip(checkbox, tooltip))
            
        return checkbox
        
    def make_slider(self, from_: float, to: float, variable: tk.DoubleVar,
                   tooltip: Optional[str] = None) -> ttk.Scale:
        """
        Create a slider with an optional tooltip.
        
        Args:
            from_: The minimum value
            to: The maximum value
            variable: The variable to bind to
            tooltip: Optional tooltip text
            
        Returns:
            The created slider
        """
        slider = ttk.Scale(self.parent, from_=from_, to=to, variable=variable,
                          orient=tk.HORIZONTAL)
        
        if tooltip:
            self.tooltips.append(Tooltip(slider, tooltip))
            
        return slider
        
    def set_enabled(self, widget: tk.Widget, enabled: bool) -> None:
        """
        Set whether a widget is enabled.
        
        Args:
            widget: The widget
            enabled: Whether the widget should be enabled
        """
        if enabled:
            widget.state(["!disabled"])
        else:
            widget.state(["disabled"])