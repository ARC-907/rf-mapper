"""
Advanced Controller for the RF Analyzer GUI.

This module contains the AdvancedController class, which handles advanced operations
such as batch processing, automation, and configuration settings.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Any, Dict, List
import numpy as np
import os
import json
from pathlib import Path

from sim_rf_map.gui.models.rf_data_model import RFDataModel
from sim_rf_map.gui.models.advanced_model import AdvancedModel
from sim_rf_map.gui.views.advanced_view import AdvancedView

class AdvancedController:
    """
    Controller for advanced operations.
    
    This class handles advanced operations such as batch processing, automation,
    and configuration settings.
    """
    
    def __init__(self, parent: tk.ttk.Frame, rf_data: RFDataModel, 
                advanced_model: AdvancedModel, main_controller: Any) -> None:
        """
        Initialize the advanced controller.
        
        Args:
            parent: The parent frame
            rf_data: The RF data model
            advanced_model: The advanced model
            main_controller: The main controller
        """
        self.rf_data = rf_data
        self.advanced_model = advanced_model
        self.main_controller = main_controller
        
        # Create view
        self.view = AdvancedView(parent)
        
        # Set up event handlers
        self._setup_event_handlers()
        
        # Event callbacks
        self.on_config_changed: Optional[Callable] = None
        self.on_batch_complete: Optional[Callable] = None
        
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.view.set_batch_process_button_command(self._start_batch_processing)
        self.view.set_export_results_button_command(self._export_results)
        self.view.set_import_config_button_command(self._import_config)
        self.view.set_export_config_button_command(self._export_config)
        self.view.set_apply_config_button_command(self._apply_config)
        self.view.set_reset_config_button_command(self._reset_config)
        self.view.set_memory_optimize_button_command(self._optimize_memory)
        self.view.set_run_automation_button_command(self._run_automation)
        
    def _start_batch_processing(self) -> None:
        """Start batch processing."""
        try:
            # Get batch settings from view
            batch_settings = self.view.get_batch_settings()
            
            # Check if input directory exists
            input_dir = batch_settings.get("input_directory")
            if not input_dir or not os.path.isdir(input_dir):
                self.main_controller.show_error("Error", "Invalid input directory")
                return
                
            # Check if output directory exists
            output_dir = batch_settings.get("output_directory")
            if not output_dir or not os.path.isdir(output_dir):
                self.main_controller.show_error("Error", "Invalid output directory")
                return
                
            # Get list of input files
            input_files = self._get_input_files(input_dir, batch_settings.get("file_pattern", "*.tif"))
            if not input_files:
                self.main_controller.show_error("Error", "No input files found")
                return
                
            # Show progress dialog
            self.main_controller.show_progress("Batch Processing", f"Processing {len(input_files)} files...")
            
            # Process files
            results = []
            for i, file_path in enumerate(input_files):
                # Update progress
                progress = (i + 1) / len(input_files)
                self.main_controller.update_progress(progress, f"Processing {i+1}/{len(input_files)}: {os.path.basename(file_path)}")
                
                # Process file
                result = self._process_single_file(file_path, output_dir, batch_settings)
                results.append(result)
                
            # Close progress dialog
            self.main_controller.hide_progress()
            
            # Show summary
            self._show_batch_summary(results)
            
            # Notify main controller
            self.main_controller.set_status(f"Batch processing completed: {len(input_files)} files processed")
            
            # Call event callback
            if self.on_batch_complete:
                self.on_batch_complete()
                
        except Exception as e:
            self.main_controller.hide_progress()
            self.main_controller.show_error("Error", f"Batch processing failed: {str(e)}")
            
    def _get_input_files(self, input_dir: str, file_pattern: str) -> List[str]:
        """
        Get a list of input files matching the pattern.
        
        Args:
            input_dir: The input directory
            file_pattern: The file pattern to match
            
        Returns:
            A list of file paths
        """
        import glob
        return glob.glob(os.path.join(input_dir, file_pattern))
        
    def _process_single_file(self, file_path: str, output_dir: str, batch_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single file in batch mode.
        
        Args:
            file_path: The input file path
            output_dir: The output directory
            batch_settings: The batch processing settings
            
        Returns:
            A dictionary with processing results
        """
        # This is a simplified implementation
        # In a real implementation, this would load the file, process it, and save the results
        
        # Create a result dictionary
        result = {
            "input_file": file_path,
            "output_file": os.path.join(output_dir, os.path.basename(file_path)),
            "success": True,
            "error": None,
            "processing_time": 0.0,
            "metrics": {}
        }
        
        try:
            # Simulate processing
            import time
            start_time = time.time()
            
            # Simulate work
            time.sleep(0.5)
            
            # Record processing time
            result["processing_time"] = time.time() - start_time
            
            # Add some metrics
            result["metrics"] = {
                "mean_loss": np.random.uniform(80, 120),
                "max_loss": np.random.uniform(120, 150),
                "coverage_percent": np.random.uniform(60, 95)
            }
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            
        return result
        
    def _show_batch_summary(self, results: List[Dict[str, Any]]) -> None:
        """
        Show a summary of batch processing results.
        
        Args:
            results: The batch processing results
        """
        # Create a new window to display results
        summary_window = tk.Toplevel(self.main_controller.root)
        summary_window.title("Batch Processing Summary")
        summary_window.geometry("600x400")
        
        # Create a frame for the results
        frame = tk.ttk.Frame(summary_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a text widget to display results
        text = tk.Text(frame, wrap=tk.WORD, width=80, height=20)
        text.pack(fill=tk.BOTH, expand=True)
        
        # Add a scrollbar
        scrollbar = tk.ttk.Scrollbar(text, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scrollbar.set)
        
        # Insert results
        text.insert(tk.END, "Batch Processing Summary\n")
        text.insert(tk.END, "=======================\n\n")
        
        # Count successes and failures
        successes = sum(1 for r in results if r.get("success", False))
        failures = len(results) - successes
        
        text.insert(tk.END, f"Total files processed: {len(results)}\n")
        text.insert(tk.END, f"Successful: {successes}\n")
        text.insert(tk.END, f"Failed: {failures}\n\n")
        
        # Calculate average processing time
        avg_time = sum(r.get("processing_time", 0) for r in results) / len(results) if results else 0
        text.insert(tk.END, f"Average processing time: {avg_time:.2f} seconds\n\n")
        
        # List failures
        if failures > 0:
            text.insert(tk.END, "Failed files:\n")
            for result in results:
                if not result.get("success", False):
                    text.insert(tk.END, f"- {os.path.basename(result['input_file'])}: {result.get('error', 'Unknown error')}\n")
            text.insert(tk.END, "\n")
            
        # Make text read-only
        text.config(state=tk.DISABLED)
        
    def _export_results(self) -> None:
        """Export the current results."""
        try:
            # Check if we have results to export
            if self.rf_data.loss_volume is None:
                self.main_controller.show_warning("Warning", "No results to export")
                return
                
            # Show file dialog
            file_path = tk.filedialog.asksaveasfilename(
                title="Export Results",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
                
            # Export results
            self.advanced_model.export_results(file_path, self.rf_data)
            
            # Notify main controller
            self.main_controller.set_status(f"Results exported to: {file_path}")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to export results: {str(e)}")
            
    def _import_config(self) -> None:
        """Import configuration from a file."""
        try:
            # Show file dialog
            file_path = tk.filedialog.askopenfilename(
                title="Import Configuration",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
                
            # Import configuration
            config = self.advanced_model.import_config(file_path)
            
            # Update view
            self.view.set_config(config)
            
            # Notify main controller
            self.main_controller.set_status(f"Configuration imported from: {file_path}")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to import configuration: {str(e)}")
            
    def _export_config(self) -> None:
        """Export configuration to a file."""
        try:
            # Get configuration from view
            config = self.view.get_config()
            
            # Show file dialog
            file_path = tk.filedialog.asksaveasfilename(
                title="Export Configuration",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
                
            # Export configuration
            self.advanced_model.export_config(file_path, config)
            
            # Notify main controller
            self.main_controller.set_status(f"Configuration exported to: {file_path}")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to export configuration: {str(e)}")
            
    def _apply_config(self) -> None:
        """Apply the current configuration."""
        try:
            # Get configuration from view
            config = self.view.get_config()
            
            # Apply configuration
            self.advanced_model.apply_config(config)
            
            # Notify main controller
            self.main_controller.set_status("Configuration applied")
            
            # Call event callback
            if self.on_config_changed:
                self.on_config_changed()
                
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to apply configuration: {str(e)}")
            
    def _reset_config(self) -> None:
        """Reset the configuration to defaults."""
        try:
            # Reset configuration
            default_config = self.advanced_model.get_default_config()
            
            # Update view
            self.view.set_config(default_config)
            
            # Notify main controller
            self.main_controller.set_status("Configuration reset to defaults")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to reset configuration: {str(e)}")
            
    def _optimize_memory(self) -> None:
        """Optimize memory usage."""
        try:
            # Get memory settings from view
            memory_settings = self.view.get_memory_settings()
            
            # Apply memory optimization
            self.advanced_model.optimize_memory(memory_settings)
            
            # Notify main controller
            self.main_controller.set_status("Memory optimization applied")
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to optimize memory: {str(e)}")
            
    def _run_automation(self) -> None:
        """Run automation script."""
        try:
            # Get automation settings from view
            automation_settings = self.view.get_automation_settings()
            
            # Check if script file exists
            script_file = automation_settings.get("script_file")
            if not script_file or not os.path.isfile(script_file):
                self.main_controller.show_error("Error", "Invalid script file")
                return
                
            # Show progress dialog
            self.main_controller.show_progress("Running Automation", "Executing script...")
            
            # Run automation
            result = self.advanced_model.run_automation(automation_settings, self.rf_data)
            
            # Close progress dialog
            self.main_controller.hide_progress()
            
            # Show result
            if result.get("success", False):
                self.main_controller.show_info("Automation Complete", result.get("message", "Script executed successfully"))
            else:
                self.main_controller.show_error("Automation Failed", result.get("error", "Unknown error"))
                
            # Notify main controller
            self.main_controller.set_status("Automation script executed")
            
        except Exception as e:
            self.main_controller.hide_progress()
            self.main_controller.show_error("Error", f"Failed to run automation: {str(e)}")
            
    def refresh(self) -> None:
        """Refresh the advanced view."""
        try:
            # Update view with current settings
            config = self.advanced_model.get_current_config()
            memory_info = self.advanced_model.get_memory_info()
            
            # Update view
            self.view.set_config(config)
            self.view.set_memory_info(memory_info)
            
        except Exception as e:
            self.main_controller.show_error("Error", f"Failed to refresh advanced view: {str(e)}")