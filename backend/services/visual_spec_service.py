"""
Battwheels Knowledge Brain - Visual Spec Service
Generates deterministic visual specifications for diagrams and charts
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DiagramType(str, Enum):
    FLOWCHART = "flowchart"
    DECISION_TREE = "decision_tree"
    SEQUENCE = "sequence"


class ChartType(str, Enum):
    GAUGE = "gauge"
    HORIZONTAL_BAR = "horizontal_bar"
    PIE = "pie"
    INFO = "info"


@dataclass
class DiagramNode:
    id: str
    label: str
    node_type: str = "default"  # start, end, decision, action


@dataclass
class DiagramEdge:
    from_id: str
    to_id: str
    label: str = ""


class VisualSpecService:
    """
    Generates visual specifications for frontend rendering.
    All visuals are deterministic - no external image downloads.
    """
    
    # ==================== MERMAID DIAGRAM GENERATORS ====================
    
    @staticmethod
    def generate_flowchart(
        title: str,
        steps: List[Dict],
        include_decision_points: bool = False
    ) -> Dict:
        """
        Generate Mermaid flowchart from diagnostic steps.
        
        Args:
            title: Chart title
            steps: List of diagnostic steps with 'action' and optional 'decision'
            include_decision_points: Add yes/no branching
        """
        if not steps:
            return None
        
        lines = ["graph TD"]
        lines.append(f"    subgraph {title.replace(' ', '_')}")
        
        for i, step in enumerate(steps[:8]):  # Max 8 nodes for readability
            node_id = f"N{i+1}"
            action = step.get("action", step.get("hinglish", f"Step {i+1}"))
            action = action[:45].replace('"', "'")  # Truncate and escape
            
            if i == 0:
                lines.append(f'    START(("🔧 Start")) --> {node_id}["{action}"]')
            else:
                prev_id = f"N{i}"
                
                # Check if previous step had a decision point
                if include_decision_points and i > 0:
                    prev_step = steps[i-1]
                    if prev_step.get("expected"):
                        # Add decision diamond
                        dec_id = f"D{i}"
                        lines.append(f'    {prev_id} --> {dec_id}{{"{prev_step.get("expected", "Check")[:20]}?"}}')
                        lines.append(f'    {dec_id} -->|Yes| {node_id}["{action}"]')
                        continue
                
                lines.append(f'    {prev_id} --> {node_id}["{action}"]')
        
        # Add end node
        last_id = f"N{min(len(steps), 8)}"
        lines.append(f'    {last_id} --> END(("✅ Done"))')
        lines.append("    end")
        
        # Styling
        lines.extend([
            "",
            "    %% Styling",
            "    classDef default fill:#1e293b,stroke:#10b981,stroke-width:2px,color:#e2e8f0",
            "    classDef start fill:#10b981,stroke:#10b981,color:#fff",
            "    classDef end fill:#10b981,stroke:#10b981,color:#fff",
            "    classDef decision fill:#f59e0b,stroke:#f59e0b,color:#000"
        ])
        
        return {
            "type": "mermaid",
            "diagram_type": DiagramType.FLOWCHART.value,
            "code": "\n".join(lines),
            "title": title
        }
    
    @staticmethod
    def generate_decision_tree(
        title: str,
        root_question: str,
        branches: List[Dict]
    ) -> Dict:
        """
        Generate decision tree for troubleshooting.
        
        Args:
            title: Tree title
            root_question: Initial diagnostic question
            branches: List of {answer, next_step, sub_branches}
        """
        lines = ["graph TD"]
        lines.append(f'    ROOT{{"{root_question[:50]}"}}')
        
        def add_branches(parent_id: str, branches: List[Dict], depth: int = 0):
            for i, branch in enumerate(branches[:4]):  # Max 4 branches per level
                node_id = f"{parent_id}_{i+1}"
                answer = branch.get("answer", f"Option {i+1}")[:15]
                next_step = branch.get("next_step", "")[:40]
                
                if branch.get("is_end"):
                    lines.append(f'    {parent_id} -->|{answer}| {node_id}(("{next_step}"))')
                elif branch.get("sub_branches") and depth < 2:
                    lines.append(f'    {parent_id} -->|{answer}| {node_id}{{"{next_step}?"}}')
                    add_branches(node_id, branch["sub_branches"], depth + 1)
                else:
                    lines.append(f'    {parent_id} -->|{answer}| {node_id}["{next_step}"]')
        
        add_branches("ROOT", branches)
        
        # Styling
        lines.extend([
            "",
            "    classDef default fill:#1e293b,stroke:#10b981,stroke-width:2px,color:#e2e8f0",
            "    classDef decision fill:#3b82f6,stroke:#3b82f6,color:#fff"
        ])
        
        return {
            "type": "mermaid",
            "diagram_type": DiagramType.DECISION_TREE.value,
            "code": "\n".join(lines),
            "title": title
        }
    
    @staticmethod
    def generate_sequence_diagram(
        title: str,
        actors: List[str],
        interactions: List[Dict]
    ) -> Dict:
        """
        Generate sequence diagram for process flows.
        """
        lines = ["sequenceDiagram"]
        
        # Define actors
        for actor in actors[:4]:
            lines.append(f"    participant {actor.replace(' ', '_')}")
        
        # Add interactions
        for interaction in interactions[:10]:
            from_actor = interaction.get("from", actors[0]).replace(" ", "_")
            to_actor = interaction.get("to", actors[-1]).replace(" ", "_")
            message = interaction.get("message", "")[:30]
            
            if interaction.get("is_response"):
                lines.append(f"    {from_actor}-->>>{to_actor}: {message}")
            else:
                lines.append(f"    {from_actor}->>>{to_actor}: {message}")
        
        return {
            "type": "mermaid",
            "diagram_type": DiagramType.SEQUENCE.value,
            "code": "\n".join(lines),
            "title": title
        }
    
    # ==================== CHART SPEC GENERATORS ====================
    
    @staticmethod
    def generate_gauge_spec(
        title: str,
        value: float,
        max_value: float = 100,
        unit: str = "%",
        zones: List[Dict] = None
    ) -> Dict:
        """
        Generate gauge chart specification.
        
        Args:
            title: Gauge title
            value: Current value
            max_value: Maximum value
            unit: Unit label
            zones: List of {min, max, color} for color zones
        """
        if zones is None:
            zones = [
                {"min": 0, "max": 10, "color": "#ef4444", "label": "Critical"},
                {"min": 10, "max": 30, "color": "#f59e0b", "label": "Low"},
                {"min": 30, "max": 100, "color": "#10b981", "label": "Normal"}
            ]
        
        # Determine current zone
        current_color = "#10b981"
        current_label = "Normal"
        for zone in zones:
            if zone["min"] <= value <= zone["max"]:
                current_color = zone["color"]
                current_label = zone.get("label", "")
                break
        
        return {
            "type": ChartType.GAUGE.value,
            "title": title,
            "value": round(value, 1),
            "max": max_value,
            "unit": unit,
            "color": current_color,
            "label": current_label,
            "zones": zones,
            "rotation": (value / max_value) * 180  # For CSS rotation
        }
    
    @staticmethod
    def generate_bar_chart_spec(
        title: str,
        data: List[Dict],
        max_value: float = 100,
        unit: str = "%",
        horizontal: bool = True
    ) -> Dict:
        """
        Generate bar chart specification.
        
        Args:
            title: Chart title
            data: List of {label, value, color?}
            max_value: Maximum value for scale
            unit: Unit label
            horizontal: Horizontal bars (True) or vertical (False)
        """
        # Ensure all items have colors
        colors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"]
        processed_data = []
        
        for i, item in enumerate(data[:6]):  # Max 6 bars
            processed_data.append({
                "label": item.get("label", f"Item {i+1}")[:25],
                "value": min(item.get("value", 0), max_value),
                "color": item.get("color", colors[i % len(colors)]),
                "percentage": (item.get("value", 0) / max_value) * 100 if max_value > 0 else 0
            })
        
        return {
            "type": ChartType.HORIZONTAL_BAR.value if horizontal else "vertical_bar",
            "title": title,
            "data": processed_data,
            "max": max_value,
            "unit": unit
        }
    
    @staticmethod
    def generate_info_card_spec(
        title: str,
        value: Any,
        unit: str = "",
        icon: str = "info",
        subtitle: str = ""
    ) -> Dict:
        """
        Generate info card specification.
        """
        return {
            "type": ChartType.INFO.value,
            "title": title,
            "value": value,
            "unit": unit,
            "icon": icon,
            "subtitle": subtitle
        }
    
    # ==================== EV-SPECIFIC VISUAL GENERATORS ====================
    
    @staticmethod
    def generate_battery_status_visual(
        soc: float,
        voltage: Optional[float] = None,
        current: Optional[float] = None,
        temperature: Optional[float] = None,
        health: Optional[float] = None
    ) -> Dict:
        """
        Generate battery status visualization.
        """
        specs = {
            "type": "battery_status",
            "components": []
        }
        
        # SOC Gauge
        specs["components"].append(
            VisualSpecService.generate_gauge_spec(
                "State of Charge",
                soc,
                100,
                "%",
                [
                    {"min": 0, "max": 10, "color": "#ef4444", "label": "Critical"},
                    {"min": 10, "max": 20, "color": "#f59e0b", "label": "Low"},
                    {"min": 20, "max": 100, "color": "#10b981", "label": "OK"}
                ]
            )
        )
        
        # Voltage (if provided)
        if voltage is not None:
            specs["components"].append(
                VisualSpecService.generate_info_card_spec(
                    "Pack Voltage",
                    round(voltage, 1),
                    "V",
                    "bolt"
                )
            )
        
        # Temperature (if provided)
        if temperature is not None:
            temp_color = "#10b981" if 15 <= temperature <= 35 else "#f59e0b" if 10 <= temperature <= 45 else "#ef4444"
            specs["components"].append({
                "type": "temperature",
                "title": "Battery Temp",
                "value": round(temperature, 1),
                "unit": "°C",
                "color": temp_color,
                "safe_range": "15-35°C"
            })
        
        # Health (if provided)
        if health is not None:
            specs["components"].append(
                VisualSpecService.generate_gauge_spec(
                    "Battery Health",
                    health,
                    100,
                    "%",
                    [
                        {"min": 0, "max": 60, "color": "#ef4444", "label": "Poor"},
                        {"min": 60, "max": 80, "color": "#f59e0b", "label": "Fair"},
                        {"min": 80, "max": 100, "color": "#10b981", "label": "Good"}
                    ]
                )
            )
        
        return specs
    
    @staticmethod
    def generate_diagnostic_progress_spec(
        completed_steps: int,
        total_steps: int,
        current_step: Optional[str] = None,
        issues_found: int = 0
    ) -> Dict:
        """
        Generate diagnostic progress visualization.
        """
        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            "type": "progress",
            "title": "Diagnostic Progress",
            "completed": completed_steps,
            "total": total_steps,
            "percentage": round(progress, 1),
            "current_step": current_step,
            "issues_found": issues_found,
            "color": "#10b981" if progress >= 100 else "#3b82f6"
        }
    
    @staticmethod
    def generate_troubleshooting_checklist_spec(
        items: List[Dict]
    ) -> Dict:
        """
        Generate troubleshooting checklist specification.
        
        Args:
            items: List of {title, checked, note, severity}
        """
        return {
            "type": "checklist",
            "title": "Diagnostic Checklist",
            "items": [
                {
                    "id": f"check_{i}",
                    "title": item.get("title", f"Step {i+1}"),
                    "checked": item.get("checked", False),
                    "note": item.get("note", ""),
                    "severity": item.get("severity", "normal"),
                    "icon": "✓" if item.get("checked") else "○"
                }
                for i, item in enumerate(items[:10])
            ],
            "completed_count": sum(1 for item in items if item.get("checked", False)),
            "total_count": len(items[:10])
        }


# ==================== PREDEFINED VISUAL TEMPLATES ====================

class EVDiagnosticTemplates:
    """Predefined visual templates for common EV diagnostic scenarios"""
    
    @staticmethod
    def battery_not_charging_flow() -> Dict:
        """Standard flow for battery not charging diagnosis"""
        steps = [
            {"action": "HV isolation check", "expected": "Isolated"},
            {"action": "12V auxiliary battery", "expected": ">12.4V"},
            {"action": "Charger LED status", "expected": "Green/Blue"},
            {"action": "Charging port inspection", "expected": "No damage"},
            {"action": "BMS communication", "expected": "Active"},
            {"action": "Cell voltage balance", "expected": "±50mV"},
            {"action": "Charger output test", "expected": "Rated voltage"}
        ]
        return VisualSpecService.generate_flowchart(
            "Battery Not Charging - Diagnostic Flow",
            steps,
            include_decision_points=True
        )
    
    @staticmethod
    def motor_not_running_flow() -> Dict:
        """Standard flow for motor not running diagnosis"""
        steps = [
            {"action": "Kill switch check", "expected": "Off"},
            {"action": "Side stand sensor", "expected": "Retracted"},
            {"action": "Throttle position", "expected": "0% at rest"},
            {"action": "Motor controller power", "expected": "Active"},
            {"action": "Hall sensor check", "expected": "3 signals"},
            {"action": "Phase resistance", "expected": "Balanced"},
            {"action": "Controller DTC read", "expected": "No faults"}
        ]
        return VisualSpecService.generate_flowchart(
            "Motor Not Running - Diagnostic Flow",
            steps,
            include_decision_points=True
        )
    
    @staticmethod
    def range_anxiety_flow() -> Dict:
        """Flow for reduced range diagnosis"""
        steps = [
            {"action": "Full charge test", "expected": "100% SOC"},
            {"action": "Cell balance check", "expected": "±50mV"},
            {"action": "Battery temp normal", "expected": "15-35°C"},
            {"action": "Tire pressure", "expected": "As specified"},
            {"action": "Brake drag check", "expected": "Free spin"},
            {"action": "Regen settings", "expected": "Enabled"}
        ]
        return VisualSpecService.generate_flowchart(
            "Reduced Range - Diagnostic Flow",
            steps
        )
