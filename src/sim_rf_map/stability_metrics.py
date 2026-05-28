"""Module for collecting and reporting stability metrics."""

import os
import re
import sys
import time
import logging
import platform
import psutil
import json
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import traceback
import inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stability_metrics')

# Paths
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"
LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"
TEMPLATE_PATH = REPORTS_DIR / "stability_report_template.md"


class StabilityMetricsCollector:
    """Collects stability metrics from logs and system monitoring."""
    
    def __init__(self):
        """Initialize the stability metrics collector."""
        self.metrics = {
            "crash_analysis": {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "crash_rate": 0.0,
                "crash_distribution": {},
                "top_crash_causes": []
            },
            "error_handling": {
                "functions_with_error_handling": 0,
                "total_functions": 0,
                "coverage_percentage": 0.0,
                "errors_encountered": 0,
                "successful_recoveries": 0,
                "recovery_rate": 0.0
            },
            "performance_metrics": {
                "response_time": {},
                "throughput": {
                    "average_ops": 0.0,
                    "peak_ops": 0.0
                }
            },
            "resource_usage": {
                "memory_usage": {
                    "average": 0.0,
                    "peak": 0.0,
                    "leak_detected": False
                },
                "cpu_usage": {
                    "average": 0.0,
                    "peak": 0.0
                },
                "disk_io": {
                    "average_read": 0.0,
                    "average_write": 0.0,
                    "peak_io": 0.0
                }
            },
            "stability_issues": {
                "critical": [],
                "major": [],
                "minor": []
            },
            "recommendations": [],
            "environment": {
                "os": platform.platform(),
                "python_version": platform.python_version(),
                "hardware_specs": self._get_hardware_specs()
            }
        }
        
        # Ensure directories exist
        REPORTS_DIR.mkdir(exist_ok=True)
        LOGS_DIR.mkdir(exist_ok=True)
    
    def _get_hardware_specs(self) -> str:
        """Get hardware specifications."""
        try:
            cpu_info = f"CPU: {platform.processor()}, Cores: {psutil.cpu_count(logical=False)}, Threads: {psutil.cpu_count()}"
            memory_info = f"Memory: {round(psutil.virtual_memory().total / (1024**3), 2)} GB"
            disk_info = f"Disk: {round(psutil.disk_usage('/').total / (1024**3), 2)} GB"
            return f"{cpu_info}, {memory_info}, {disk_info}"
        except Exception as e:
            logger.error(f"Error getting hardware specs: {str(e)}")
            return "Unknown"
    
    def collect_crash_metrics(self) -> None:
        """Collect crash metrics from log files."""
        logger.info("Collecting crash metrics...")
        
        # Find all log files
        log_files = list(LOGS_DIR.glob("*.log"))
        
        # Initialize counters
        total_runs = len(log_files)
        failed_runs = 0
        crash_distribution = {}
        crash_causes = {}
        
        # Process each log file
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                    # Check if the log contains a crash
                    if "Traceback" in content or "ERROR" in content or "CRITICAL" in content:
                        failed_runs += 1
                        
                        # Extract component from log filename
                        component = log_file.stem.split('_')[-1]
                        crash_distribution[component] = crash_distribution.get(component, 0) + 1
                        
                        # Extract crash cause
                        crash_cause = self._extract_crash_cause(content)
                        if crash_cause:
                            crash_causes[crash_cause] = crash_causes.get(crash_cause, 0) + 1
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {str(e)}")
        
        # Calculate crash rate
        successful_runs = total_runs - failed_runs
        crash_rate = (failed_runs / total_runs) * 100 if total_runs > 0 else 0.0
        
        # Sort crash causes by frequency
        top_crash_causes = sorted(crash_causes.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Update metrics
        self.metrics["crash_analysis"]["total_runs"] = total_runs
        self.metrics["crash_analysis"]["successful_runs"] = successful_runs
        self.metrics["crash_analysis"]["failed_runs"] = failed_runs
        self.metrics["crash_analysis"]["crash_rate"] = crash_rate
        self.metrics["crash_analysis"]["crash_distribution"] = crash_distribution
        self.metrics["crash_analysis"]["top_crash_causes"] = top_crash_causes
    
    def _extract_crash_cause(self, log_content: str) -> Optional[str]:
        """Extract the crash cause from a log file."""
        # Look for exception in traceback
        traceback_match = re.search(r"Traceback.*?([A-Za-z0-9_]+Error:.*?)(?:\n\n|\Z)", log_content, re.DOTALL)
        if traceback_match:
            return traceback_match.group(1).strip().split('\n')[0]
        
        # Look for ERROR or CRITICAL log entries
        error_match = re.search(r"ERROR.*?:(.*?)(?:\n|$)", log_content)
        if error_match:
            return error_match.group(1).strip()
        
        critical_match = re.search(r"CRITICAL.*?:(.*?)(?:\n|$)", log_content)
        if critical_match:
            return critical_match.group(1).strip()
        
        return None
    
    def collect_error_handling_metrics(self) -> None:
        """Collect error handling metrics from source code."""
        logger.info("Collecting error handling metrics...")
        
        # Get the source directory
        src_dir = Path(__file__).resolve().parents[0]
        
        # Initialize counters
        total_functions = 0
        functions_with_error_handling = 0
        
        # Process each Python file
        for py_file in src_dir.glob("**/*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    
                    # Count functions
                    function_matches = re.findall(r"def\s+([a-zA-Z0-9_]+)\s*\(", content)
                    total_functions += len(function_matches)
                    
                    # Count functions with error handling
                    for func_name in function_matches:
                        # Find the function definition
                        func_pattern = re.compile(r"def\s+" + re.escape(func_name) + r"\s*\(.*?(?=def|\Z)", re.DOTALL)
                        func_match = func_pattern.search(content)
                        if func_match:
                            func_code = func_match.group(0)
                            # Check if the function has try-except blocks
                            if re.search(r"try\s*:", func_code) and re.search(r"except\s+", func_code):
                                functions_with_error_handling += 1
            except Exception as e:
                logger.error(f"Error processing file {py_file}: {str(e)}")
        
        # Calculate coverage percentage
        coverage_percentage = (functions_with_error_handling / total_functions) * 100 if total_functions > 0 else 0.0
        
        # Update metrics
        self.metrics["error_handling"]["functions_with_error_handling"] = functions_with_error_handling
        self.metrics["error_handling"]["total_functions"] = total_functions
        self.metrics["error_handling"]["coverage_percentage"] = coverage_percentage
        
        # Collect error recovery metrics from logs
        errors_encountered = 0
        successful_recoveries = 0
        
        # Process each log file
        for log_file in LOGS_DIR.glob("*.log"):
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                    # Count errors
                    error_matches = re.findall(r"ERROR.*?:", content)
                    errors_encountered += len(error_matches)
                    
                    # Count successful recoveries
                    recovery_matches = re.findall(r"Recovered from error", content, re.IGNORECASE)
                    successful_recoveries += len(recovery_matches)
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {str(e)}")
        
        # Calculate recovery rate
        recovery_rate = (successful_recoveries / errors_encountered) * 100 if errors_encountered > 0 else 0.0
        
        # Update metrics
        self.metrics["error_handling"]["errors_encountered"] = errors_encountered
        self.metrics["error_handling"]["successful_recoveries"] = successful_recoveries
        self.metrics["error_handling"]["recovery_rate"] = recovery_rate
    
    def collect_performance_metrics(self) -> None:
        """Collect performance metrics from log files."""
        logger.info("Collecting performance metrics...")
        
        # Initialize performance data
        operations = {}
        throughput_data = []
        
        # Process each log file
        for log_file in LOGS_DIR.glob("*.log"):
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                    # Extract operation timing information
                    timing_matches = re.findall(r"Operation '([^']+)' completed in (\d+\.?\d*) ms", content)
                    for operation, time_ms in timing_matches:
                        if operation not in operations:
                            operations[operation] = []
                        operations[operation].append(float(time_ms))
                    
                    # Extract throughput information
                    throughput_matches = re.findall(r"Throughput: (\d+\.?\d*) operations per second", content)
                    for ops in throughput_matches:
                        throughput_data.append(float(ops))
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {str(e)}")
        
        # Calculate response time metrics
        response_time = {}
        for operation, times in operations.items():
            if times:
                times.sort()
                avg_time = sum(times) / len(times)
                percentile_90 = times[int(len(times) * 0.9)] if len(times) >= 10 else times[-1]
                max_time = times[-1]
                
                response_time[operation] = {
                    "average": avg_time,
                    "percentile_90": percentile_90,
                    "maximum": max_time
                }
        
        # Calculate throughput metrics
        avg_ops = sum(throughput_data) / len(throughput_data) if throughput_data else 0.0
        peak_ops = max(throughput_data) if throughput_data else 0.0
        
        # Update metrics
        self.metrics["performance_metrics"]["response_time"] = response_time
        self.metrics["performance_metrics"]["throughput"]["average_ops"] = avg_ops
        self.metrics["performance_metrics"]["throughput"]["peak_ops"] = peak_ops
    
    def collect_resource_usage_metrics(self) -> None:
        """Collect resource usage metrics from log files."""
        logger.info("Collecting resource usage metrics...")
        
        # Initialize resource usage data
        memory_usage = []
        cpu_usage = []
        disk_read = []
        disk_write = []
        
        # Process each log file
        for log_file in LOGS_DIR.glob("*.log"):
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                    # Extract memory usage information
                    memory_matches = re.findall(r"Memory usage: (\d+\.?\d*) MB", content)
                    for memory in memory_matches:
                        memory_usage.append(float(memory))
                    
                    # Extract CPU usage information
                    cpu_matches = re.findall(r"CPU usage: (\d+\.?\d*)%", content)
                    for cpu in cpu_matches:
                        cpu_usage.append(float(cpu))
                    
                    # Extract disk I/O information
                    disk_read_matches = re.findall(r"Disk read: (\d+\.?\d*) MB/s", content)
                    for read in disk_read_matches:
                        disk_read.append(float(read))
                    
                    disk_write_matches = re.findall(r"Disk write: (\d+\.?\d*) MB/s", content)
                    for write in disk_write_matches:
                        disk_write.append(float(write))
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {str(e)}")
        
        # Calculate memory usage metrics
        avg_memory = sum(memory_usage) / len(memory_usage) if memory_usage else 0.0
        peak_memory = max(memory_usage) if memory_usage else 0.0
        
        # Check for memory leaks
        memory_leak_detected = False
        if len(memory_usage) >= 10:
            # Check if memory usage is consistently increasing
            increasing_count = sum(1 for i in range(1, len(memory_usage)) if memory_usage[i] > memory_usage[i-1])
            if increasing_count / len(memory_usage) > 0.8:
                memory_leak_detected = True
        
        # Calculate CPU usage metrics
        avg_cpu = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0.0
        peak_cpu = max(cpu_usage) if cpu_usage else 0.0
        
        # Calculate disk I/O metrics
        avg_read = sum(disk_read) / len(disk_read) if disk_read else 0.0
        avg_write = sum(disk_write) / len(disk_write) if disk_write else 0.0
        peak_io = max(disk_read + disk_write) if disk_read or disk_write else 0.0
        
        # Update metrics
        self.metrics["resource_usage"]["memory_usage"]["average"] = avg_memory
        self.metrics["resource_usage"]["memory_usage"]["peak"] = peak_memory
        self.metrics["resource_usage"]["memory_usage"]["leak_detected"] = memory_leak_detected
        self.metrics["resource_usage"]["cpu_usage"]["average"] = avg_cpu
        self.metrics["resource_usage"]["cpu_usage"]["peak"] = peak_cpu
        self.metrics["resource_usage"]["disk_io"]["average_read"] = avg_read
        self.metrics["resource_usage"]["disk_io"]["average_write"] = avg_write
        self.metrics["resource_usage"]["disk_io"]["peak_io"] = peak_io
    
    def identify_stability_issues(self) -> None:
        """Identify stability issues based on collected metrics."""
        logger.info("Identifying stability issues...")
        
        # Critical issues
        if self.metrics["crash_analysis"]["crash_rate"] > 5.0:
            self.metrics["stability_issues"]["critical"].append(
                f"High crash rate: {self.metrics['crash_analysis']['crash_rate']:.2f}%"
            )
        
        if self.metrics["error_handling"]["coverage_percentage"] < 50.0:
            self.metrics["stability_issues"]["critical"].append(
                f"Low error handling coverage: {self.metrics['error_handling']['coverage_percentage']:.2f}%"
            )
        
        if self.metrics["resource_usage"]["memory_usage"]["leak_detected"]:
            self.metrics["stability_issues"]["critical"].append(
                "Memory leak detected"
            )
        
        # Major issues
        if 1.0 < self.metrics["crash_analysis"]["crash_rate"] <= 5.0:
            self.metrics["stability_issues"]["major"].append(
                f"Moderate crash rate: {self.metrics['crash_analysis']['crash_rate']:.2f}%"
            )
        
        if 50.0 <= self.metrics["error_handling"]["coverage_percentage"] < 70.0:
            self.metrics["stability_issues"]["major"].append(
                f"Moderate error handling coverage: {self.metrics['error_handling']['coverage_percentage']:.2f}%"
            )
        
        if self.metrics["resource_usage"]["memory_usage"]["peak"] > 1000.0:
            self.metrics["stability_issues"]["major"].append(
                f"High peak memory usage: {self.metrics['resource_usage']['memory_usage']['peak']:.2f} MB"
            )
        
        if self.metrics["resource_usage"]["cpu_usage"]["peak"] > 90.0:
            self.metrics["stability_issues"]["major"].append(
                f"High peak CPU usage: {self.metrics['resource_usage']['cpu_usage']['peak']:.2f}%"
            )
        
        # Minor issues
        if 0.1 < self.metrics["crash_analysis"]["crash_rate"] <= 1.0:
            self.metrics["stability_issues"]["minor"].append(
                f"Low crash rate: {self.metrics['crash_analysis']['crash_rate']:.2f}%"
            )
        
        if 70.0 <= self.metrics["error_handling"]["coverage_percentage"] < 90.0:
            self.metrics["stability_issues"]["minor"].append(
                f"Good error handling coverage: {self.metrics['error_handling']['coverage_percentage']:.2f}%"
            )
        
        if 500.0 < self.metrics["resource_usage"]["memory_usage"]["peak"] <= 1000.0:
            self.metrics["stability_issues"]["minor"].append(
                f"Moderate peak memory usage: {self.metrics['resource_usage']['memory_usage']['peak']:.2f} MB"
            )
    
    def generate_recommendations(self) -> None:
        """Generate recommendations based on identified issues."""
        logger.info("Generating recommendations...")
        
        # Recommendations for critical issues
        for issue in self.metrics["stability_issues"]["critical"]:
            if "crash rate" in issue:
                self.metrics["recommendations"].append(
                    "Implement comprehensive error handling and crash recovery mechanisms"
                )
            elif "error handling coverage" in issue:
                self.metrics["recommendations"].append(
                    "Increase error handling coverage by adding try-except blocks to critical functions"
                )
            elif "memory leak" in issue:
                self.metrics["recommendations"].append(
                    "Investigate and fix memory leaks by profiling the application"
                )
        
        # Recommendations for major issues
        for issue in self.metrics["stability_issues"]["major"]:
            if "crash rate" in issue:
                self.metrics["recommendations"].append(
                    "Improve error handling in frequently used components"
                )
            elif "error handling coverage" in issue:
                self.metrics["recommendations"].append(
                    "Add error handling to high-risk functions"
                )
            elif "memory usage" in issue:
                self.metrics["recommendations"].append(
                    "Optimize memory usage by reducing unnecessary object creation"
                )
            elif "CPU usage" in issue:
                self.metrics["recommendations"].append(
                    "Optimize CPU-intensive operations"
                )
        
        # General recommendations
        if not self.metrics["recommendations"]:
            self.metrics["recommendations"].append(
                "Continue monitoring application stability"
            )
            self.metrics["recommendations"].append(
                "Implement automated stability testing"
            )
            self.metrics["recommendations"].append(
                "Document error handling best practices"
            )
    
    def calculate_overall_rating(self) -> str:
        """Calculate the overall stability rating."""
        logger.info("Calculating overall stability rating...")
        
        # Calculate scores for each category
        crash_score = 100 - self.metrics["crash_analysis"]["crash_rate"]
        error_handling_score = self.metrics["error_handling"]["coverage_percentage"]
        
        # Calculate performance score
        performance_score = 0.0
        if self.metrics["performance_metrics"]["response_time"]:
            # Average response time across all operations
            avg_times = [op["average"] for op in self.metrics["performance_metrics"]["response_time"].values()]
            avg_response_time = sum(avg_times) / len(avg_times) if avg_times else 0.0
            
            # Score based on response time (lower is better)
            if avg_response_time < 100:
                performance_score = 100
            elif avg_response_time < 500:
                performance_score = 80
            elif avg_response_time < 1000:
                performance_score = 60
            elif avg_response_time < 2000:
                performance_score = 40
            else:
                performance_score = 20
        
        # Calculate resource usage score
        resource_score = 0.0
        if self.metrics["resource_usage"]["memory_usage"]["leak_detected"]:
            resource_score = 0.0
        else:
            memory_score = 100 - min(100, self.metrics["resource_usage"]["memory_usage"]["peak"] / 10)
            cpu_score = 100 - self.metrics["resource_usage"]["cpu_usage"]["peak"]
            resource_score = (memory_score + cpu_score) / 2
        
        # Calculate overall score
        overall_score = (crash_score * 0.4 + error_handling_score * 0.3 + 
                         performance_score * 0.15 + resource_score * 0.15)
        
        # Determine rating
        if overall_score >= 90:
            rating = "Excellent"
        elif overall_score >= 80:
            rating = "Good"
        elif overall_score >= 70:
            rating = "Satisfactory"
        elif overall_score >= 60:
            rating = "Fair"
        elif overall_score >= 50:
            rating = "Poor"
        else:
            rating = "Critical"
        
        # Update metrics
        self.metrics["performance_score"] = performance_score
        self.metrics["resource_usage_efficiency"] = resource_score
        
        return f"{rating} ({overall_score:.2f}/100)"
    
    def collect_all_metrics(self) -> None:
        """Collect all stability metrics."""
        logger.info("Collecting all stability metrics...")
        
        self.collect_crash_metrics()
        self.collect_error_handling_metrics()
        self.collect_performance_metrics()
        self.collect_resource_usage_metrics()
        self.identify_stability_issues()
        self.generate_recommendations()
        
        # Calculate overall rating
        rating = self.calculate_overall_rating()
        self.metrics["rating"] = rating
    
    def generate_report(self) -> str:
        """Generate a stability report based on collected metrics."""
        logger.info("Generating stability report...")
        
        # Read the template
        try:
            with open(TEMPLATE_PATH, 'r') as f:
                template = f.read()
        except Exception as e:
            logger.error(f"Error reading template: {str(e)}")
            return ""
        
        # Replace placeholders with actual values
        report = template
        
        # Executive Summary
        report = report.replace("[RATING]", self.metrics.get("rating", "N/A"))
        report = report.replace("[CRASH_RATE]", f"{self.metrics['crash_analysis']['crash_rate']:.2f}%")
        report = report.replace("[ERROR_HANDLING_COVERAGE]", f"{self.metrics['error_handling']['coverage_percentage']:.2f}%")
        report = report.replace("[PERFORMANCE_SCORE]", f"{self.metrics['performance_score']:.2f}/100")
        report = report.replace("[RESOURCE_USAGE_EFFICIENCY]", f"{self.metrics['resource_usage_efficiency']:.2f}/100")
        
        # Crash Analysis
        report = report.replace("[TOTAL_RUNS]", str(self.metrics['crash_analysis']['total_runs']))
        report = report.replace("[SUCCESSFUL_RUNS]", str(self.metrics['crash_analysis']['successful_runs']))
        report = report.replace("[FAILED_RUNS]", str(self.metrics['crash_analysis']['failed_runs']))
        
        # Crash Distribution
        crash_distribution = self.metrics['crash_analysis']['crash_distribution']
        if crash_distribution:
            crash_dist_table = ""
            for i, (component, crashes) in enumerate(sorted(crash_distribution.items(), key=lambda x: x[1], reverse=True)[:3], 1):
                percentage = (crashes / self.metrics['crash_analysis']['failed_runs']) * 100 if self.metrics['crash_analysis']['failed_runs'] > 0 else 0
                crash_dist_table += f"| {component} | {crashes} | {percentage:.2f}% |\n"
            report = report.replace("| [COMPONENT_1] | [CRASHES_1] | [PERCENTAGE_1] |\n| [COMPONENT_2] | [CRASHES_2] | [PERCENTAGE_2] |\n| [COMPONENT_3] | [CRASHES_3] | [PERCENTAGE_3] |", crash_dist_table.rstrip())
        
        # Top Crash Causes
        top_crash_causes = self.metrics['crash_analysis']['top_crash_causes']
        if top_crash_causes:
            crash_causes_list = ""
            for i, (cause, count) in enumerate(top_crash_causes, 1):
                crash_causes_list += f"{i}. {cause} - {count} occurrences\n"
            report = report.replace("1. [CRASH_CAUSE_1] - [CRASH_COUNT_1] occurrences\n2. [CRASH_CAUSE_2] - [CRASH_COUNT_2] occurrences\n3. [CRASH_CAUSE_3] - [CRASH_COUNT_3] occurrences", crash_causes_list.rstrip())
        
        # Error Handling
        report = report.replace("[FUNCTIONS_WITH_ERROR_HANDLING]", str(self.metrics['error_handling']['functions_with_error_handling']))
        report = report.replace("[TOTAL_FUNCTIONS]", str(self.metrics['error_handling']['total_functions']))
        report = report.replace("[ERRORS_ENCOUNTERED]", str(self.metrics['error_handling']['errors_encountered']))
        report = report.replace("[SUCCESSFUL_RECOVERIES]", str(self.metrics['error_handling']['successful_recoveries']))
        report = report.replace("[RECOVERY_RATE]", f"{self.metrics['error_handling']['recovery_rate']:.2f}%")
        
        # Performance Metrics
        response_time = self.metrics['performance_metrics']['response_time']
        if response_time:
            response_time_table = ""
            for i, (operation, times) in enumerate(sorted(response_time.items(), key=lambda x: x[1]['average']), 1):
                response_time_table += f"| {operation} | {times['average']:.2f} | {times['percentile_90']:.2f} | {times['maximum']:.2f} |\n"
            report = report.replace("| [OPERATION_1] | [AVG_TIME_1] | [90TH_TIME_1] | [MAX_TIME_1] |\n| [OPERATION_2] | [AVG_TIME_2] | [90TH_TIME_2] | [MAX_TIME_2] |\n| [OPERATION_3] | [AVG_TIME_3] | [90TH_TIME_3] | [MAX_TIME_3] |", response_time_table.rstrip())
        
        report = report.replace("[OPS]", f"{self.metrics['performance_metrics']['throughput']['average_ops']:.2f}")
        report = report.replace("[PEAK_OPS]", f"{self.metrics['performance_metrics']['throughput']['peak_ops']:.2f}")
        
        # Resource Usage
        report = report.replace("[AVG_MEMORY]", f"{self.metrics['resource_usage']['memory_usage']['average']:.2f}")
        report = report.replace("[PEAK_MEMORY]", f"{self.metrics['resource_usage']['memory_usage']['peak']:.2f}")
        report = report.replace("[MEMORY_LEAK_STATUS]", "Detected" if self.metrics['resource_usage']['memory_usage']['leak_detected'] else "Not Detected")
        report = report.replace("[AVG_CPU]", f"{self.metrics['resource_usage']['cpu_usage']['average']:.2f}")
        report = report.replace("[PEAK_CPU]", f"{self.metrics['resource_usage']['cpu_usage']['peak']:.2f}")
        report = report.replace("[AVG_READ]", f"{self.metrics['resource_usage']['disk_io']['average_read']:.2f}")
        report = report.replace("[AVG_WRITE]", f"{self.metrics['resource_usage']['disk_io']['average_write']:.2f}")
        report = report.replace("[PEAK_IO]", f"{self.metrics['resource_usage']['disk_io']['peak_io']:.2f}")
        
        # Stability Issues
        critical_issues = self.metrics['stability_issues']['critical']
        if critical_issues:
            critical_issues_list = ""
            for i, issue in enumerate(critical_issues, 1):
                critical_issues_list += f"{i}. {issue}\n"
            report = report.replace("1. [CRITICAL_ISSUE_1]\n2. [CRITICAL_ISSUE_2]\n3. [CRITICAL_ISSUE_3]", critical_issues_list.rstrip())
        else:
            report = report.replace("1. [CRITICAL_ISSUE_1]\n2. [CRITICAL_ISSUE_2]\n3. [CRITICAL_ISSUE_3]", "No critical issues identified")
        
        major_issues = self.metrics['stability_issues']['major']
        if major_issues:
            major_issues_list = ""
            for i, issue in enumerate(major_issues, 1):
                major_issues_list += f"{i}. {issue}\n"
            report = report.replace("1. [MAJOR_ISSUE_1]\n2. [MAJOR_ISSUE_2]\n3. [MAJOR_ISSUE_3]", major_issues_list.rstrip())
        else:
            report = report.replace("1. [MAJOR_ISSUE_1]\n2. [MAJOR_ISSUE_2]\n3. [MAJOR_ISSUE_3]", "No major issues identified")
        
        minor_issues = self.metrics['stability_issues']['minor']
        if minor_issues:
            minor_issues_list = ""
            for i, issue in enumerate(minor_issues, 1):
                minor_issues_list += f"{i}. {issue}\n"
            report = report.replace("1. [MINOR_ISSUE_1]\n2. [MINOR_ISSUE_2]\n3. [MINOR_ISSUE_3]", minor_issues_list.rstrip())
        else:
            report = report.replace("1. [MINOR_ISSUE_1]\n2. [MINOR_ISSUE_2]\n3. [MINOR_ISSUE_3]", "No minor issues identified")
        
        # Recommendations
        recommendations = self.metrics['recommendations']
        if recommendations:
            recommendations_list = ""
            for i, recommendation in enumerate(recommendations, 1):
                recommendations_list += f"{i}. {recommendation}\n"
            report = report.replace("1. [RECOMMENDATION_1]\n2. [RECOMMENDATION_2]\n3. [RECOMMENDATION_3]", recommendations_list.rstrip())
        
        # Conclusion
        conclusion = f"The OnyxGeoImage application has an overall stability rating of {self.metrics.get('rating', 'N/A')}. "
        if self.metrics['crash_analysis']['crash_rate'] > 5.0:
            conclusion += "The high crash rate is a significant concern that needs immediate attention. "
        elif self.metrics['crash_analysis']['crash_rate'] > 1.0:
            conclusion += "The moderate crash rate indicates room for improvement in application stability. "
        else:
            conclusion += "The low crash rate indicates good application stability. "
        
        if self.metrics['error_handling']['coverage_percentage'] < 50.0:
            conclusion += "Error handling coverage is insufficient and should be improved. "
        elif self.metrics['error_handling']['coverage_percentage'] < 70.0:
            conclusion += "Error handling coverage is moderate and could be improved. "
        else:
            conclusion += "Error handling coverage is good. "
        
        conclusion += "By addressing the identified issues and implementing the recommendations, the stability of the application can be further improved."
        
        report = report.replace("[CONCLUSION]", conclusion)
        
        # Environment
        report = report.replace("[OS]", self.metrics['environment']['os'])
        report = report.replace("[PYTHON_VERSION]", self.metrics['environment']['python_version'])
        report = report.replace("[HARDWARE_SPECS]", self.metrics['environment']['hardware_specs'])
        
        # Methodology
        methodology = """
The stability metrics were collected using automated tools that analyze:
1. Log files to identify crashes and errors
2. Source code to assess error handling coverage
3. Performance logs to measure response time and throughput
4. Resource usage logs to monitor memory, CPU, and disk I/O

The data was collected over the entire application lifetime and analyzed to identify patterns and issues.
"""
        report = report.replace("[METHODOLOGY]", methodology.strip())
        
        # Raw Data
        raw_data = f"Raw metrics data is available in JSON format upon request."
        report = report.replace("[RAW_DATA]", raw_data)
        
        return report
    
    def save_report(self, report: str) -> Path:
        """Save the stability report to a file."""
        logger.info("Saving stability report...")
        
        # Create the report filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        report_path = REPORTS_DIR / f"stability_report_{timestamp}.md"
        
        # Save the report
        try:
            with open(report_path, 'w') as f:
                f.write(report)
            logger.info(f"Stability report saved to {report_path}")
            return report_path
        except Exception as e:
            logger.error(f"Error saving stability report: {str(e)}")
            return None
    
    def save_metrics_json(self) -> Path:
        """Save the raw metrics data to a JSON file."""
        logger.info("Saving raw metrics data...")
        
        # Create the metrics filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        metrics_path = REPORTS_DIR / f"stability_metrics_{timestamp}.json"
        
        # Save the metrics
        try:
            with open(metrics_path, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            logger.info(f"Raw metrics data saved to {metrics_path}")
            return metrics_path
        except Exception as e:
            logger.error(f"Error saving raw metrics data: {str(e)}")
            return None


def generate_stability_report() -> Path:
    """Generate a stability report."""
    try:
        # Create a stability metrics collector
        collector = StabilityMetricsCollector()
        
        # Collect all metrics
        collector.collect_all_metrics()
        
        # Generate the report
        report = collector.generate_report()
        
        # Save the report
        report_path = collector.save_report(report)
        
        # Save the raw metrics data
        collector.save_metrics_json()
        
        return report_path
    except Exception as e:
        logger.error(f"Error generating stability report: {str(e)}")
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    report_path = generate_stability_report()
    if report_path:
        print(f"Stability report generated: {report_path}")
    else:
        print("Failed to generate stability report")
        sys.exit(1)