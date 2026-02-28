"""
EFI Seed Data - 15 Failure Cards with Decision Trees
Categories: Battery, Electrical, Controller, Motor
Each card has complete diagnostic decision tree with PASS/FAIL branching
"""
import asyncio
from datetime import datetime, timezone
import uuid


def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ==================== BATTERY SYSTEM FAILURE CARDS ====================

BATTERY_CARDS = [
    {
        "failure_id": generate_id("FC"),
        "title": "BMS Lock After Battery Swap",
        "subsystem_category": "battery",
        "failure_mode": "complete_failure",
        "symptom_text": "Vehicle not starting after battery replacement. BMS showing lock state. No communication with new battery pack.",
        "error_codes": ["E101", "E102", "BMS_LOCK"],
        "root_cause": "BMS pairing mismatch between controller and new battery",
        "root_cause_details": "Battery Management System requires re-pairing when battery pack is swapped. The new pack's ID is not registered with the vehicle controller.",
        "keywords": ["bms", "lock", "battery swap", "pairing", "not starting", "new battery"],
        "status": "approved",
        "confidence_score": 0.92,
        "usage_count": 45,
        "success_count": 42,
        "effectiveness_score": 0.93,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Check if error code E101 or E102 is displayed on dashboard",
                    "expected_measurement": "Error code visible on display",
                    "tools_required": [],
                    "pass_action": "next",
                    "fail_action": "resolution:res_other"
                },
                {
                    "order": 2,
                    "instruction": "Connect diagnostic tool and check BMS communication status",
                    "expected_measurement": "BMS status: LOCKED or NO_COMM",
                    "tools_required": ["Diagnostic scanner", "OBD cable"],
                    "reference_image": "/images/diagnostics/bms_scanner_connect.png",
                    "pass_action": "next",
                    "fail_action": "resolution:res_comm_issue"
                },
                {
                    "order": 3,
                    "instruction": "Verify battery pack connector is properly seated",
                    "expected_measurement": "Connector fully inserted, locking tab engaged",
                    "tools_required": ["Flashlight"],
                    "safety_notes": "Ensure ignition is OFF before checking connectors",
                    "pass_action": "next",
                    "fail_action": "resolution:res_connector"
                },
                {
                    "order": 4,
                    "instruction": "Initiate BMS re-pairing procedure via diagnostic tool",
                    "expected_measurement": "Pairing successful message",
                    "tools_required": ["Diagnostic scanner"],
                    "reference_image": "/images/diagnostics/bms_pairing_screen.png",
                    "pass_action": "resolution:res_success",
                    "fail_action": "resolution:res_replace_bms"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_success",
                    "title": "BMS Re-pairing Successful",
                    "description": "Battery successfully paired with controller. Vehicle should start normally.",
                    "parts_required": [],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.95
                },
                {
                    "resolution_id": "res_connector",
                    "title": "Connector Reseating Required",
                    "description": "Battery connector was not properly seated. Clean and reseat connector.",
                    "parts_required": [{"name": "Contact cleaner", "quantity": 1, "price": 250}],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.90
                },
                {
                    "resolution_id": "res_comm_issue",
                    "title": "Communication Cable Issue",
                    "description": "BMS communication cable faulty. Replace communication harness.",
                    "parts_required": [{"name": "BMS Communication Cable", "quantity": 1, "price": 1500}],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.88
                },
                {
                    "resolution_id": "res_replace_bms",
                    "title": "BMS Module Replacement",
                    "description": "BMS module faulty. Replace BMS control unit.",
                    "parts_required": [{"name": "BMS Control Unit", "quantity": 1, "price": 8500}],
                    "labor_hours": 2.0,
                    "expected_time_minutes": 120,
                    "success_rate": 0.92
                },
                {
                    "resolution_id": "res_other",
                    "title": "Further Investigation Required",
                    "description": "Issue does not match expected pattern. Escalate to senior technician.",
                    "parts_required": [],
                    "labor_hours": 1.0,
                    "expected_time_minutes": 60,
                    "success_rate": 0.70
                }
            ]
        }
    },
    {
        "failure_id": generate_id("FC"),
        "title": "Charging Failure - No Response",
        "subsystem_category": "battery",
        "failure_mode": "no_response",
        "symptom_text": "Vehicle not charging when plugged in. No indicator lights on charger. Battery SOC not increasing.",
        "error_codes": ["CHG_ERR", "E201"],
        "root_cause": "Charger communication or power supply failure",
        "root_cause_details": "Onboard charger not receiving power or communication handshake failing with charging station.",
        "keywords": ["charging", "not charging", "charger", "plug", "no response", "soc"],
        "status": "approved",
        "confidence_score": 0.89,
        "usage_count": 62,
        "success_count": 55,
        "effectiveness_score": 0.89,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Check charging station/outlet is working with another device",
                    "expected_measurement": "Power available at outlet (230V AC)",
                    "tools_required": ["Multimeter"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_external_power"
                },
                {
                    "order": 2,
                    "instruction": "Inspect charging port for damage, debris, or corrosion",
                    "expected_measurement": "Clean, undamaged pins",
                    "tools_required": ["Flashlight", "Contact cleaner"],
                    "reference_image": "/images/diagnostics/charging_port_inspection.png",
                    "pass_action": "next",
                    "fail_action": "resolution:res_port_damage"
                },
                {
                    "order": 3,
                    "instruction": "Check charging cable continuity",
                    "expected_measurement": "Continuity on all pins",
                    "tools_required": ["Multimeter"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_cable"
                },
                {
                    "order": 4,
                    "instruction": "Check onboard charger fuse",
                    "expected_measurement": "Fuse intact, continuity present",
                    "tools_required": ["Multimeter", "Fuse puller"],
                    "safety_notes": "Disconnect battery before checking fuse",
                    "pass_action": "next",
                    "fail_action": "resolution:res_fuse"
                },
                {
                    "order": 5,
                    "instruction": "Test onboard charger with diagnostic tool",
                    "expected_measurement": "Charger responds to commands",
                    "tools_required": ["Diagnostic scanner"],
                    "pass_action": "resolution:res_software",
                    "fail_action": "resolution:res_charger_replace"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_external_power",
                    "title": "External Power Issue",
                    "description": "Issue with charging station or power outlet. Advise customer to use different charging point.",
                    "parts_required": [],
                    "labor_hours": 0.25,
                    "expected_time_minutes": 15,
                    "success_rate": 1.0
                },
                {
                    "resolution_id": "res_port_damage",
                    "title": "Charging Port Repair",
                    "description": "Charging port damaged or corroded. Clean or replace port assembly.",
                    "parts_required": [{"name": "Charging Port Assembly", "quantity": 1, "price": 3500}],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.92
                },
                {
                    "resolution_id": "res_cable",
                    "title": "Charging Cable Replacement",
                    "description": "Charging cable internal break. Replace cable.",
                    "parts_required": [{"name": "OEM Charging Cable", "quantity": 1, "price": 2500}],
                    "labor_hours": 0.25,
                    "expected_time_minutes": 15,
                    "success_rate": 0.98
                },
                {
                    "resolution_id": "res_fuse",
                    "title": "Charger Fuse Replacement",
                    "description": "Charger fuse blown. Replace fuse and check for underlying issues.",
                    "parts_required": [{"name": "Charger Fuse 30A", "quantity": 2, "price": 150}],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.85
                },
                {
                    "resolution_id": "res_charger_replace",
                    "title": "Onboard Charger Replacement",
                    "description": "Onboard charger module faulty. Replace charger unit.",
                    "parts_required": [{"name": "Onboard Charger Module", "quantity": 1, "price": 15000}],
                    "labor_hours": 2.5,
                    "expected_time_minutes": 150,
                    "success_rate": 0.94
                },
                {
                    "resolution_id": "res_software",
                    "title": "Charger Software Update",
                    "description": "Charger firmware issue. Update firmware via diagnostic tool.",
                    "parts_required": [],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.88
                }
            ]
        }
    },
    {
        "failure_id": generate_id("FC"),
        "title": "Battery Communication Loss",
        "subsystem_category": "battery",
        "failure_mode": "no_response",
        "symptom_text": "Dashboard showing battery communication error. SOC display stuck or showing dashes. Vehicle in limp mode.",
        "error_codes": ["E103", "CAN_ERR", "BAT_COMM"],
        "root_cause": "CAN bus communication failure between BMS and controller",
        "root_cause_details": "Communication line between battery management system and vehicle controller interrupted or corrupted.",
        "keywords": ["communication", "can bus", "limp mode", "dashes", "soc stuck", "error"],
        "status": "approved",
        "confidence_score": 0.87,
        "usage_count": 38,
        "success_count": 33,
        "effectiveness_score": 0.87,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Read error codes from vehicle ECU",
                    "expected_measurement": "CAN_ERR or BAT_COMM code present",
                    "tools_required": ["Diagnostic scanner"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_other_issue"
                },
                {
                    "order": 2,
                    "instruction": "Check CAN bus termination resistance",
                    "expected_measurement": "60 ohms between CAN_H and CAN_L",
                    "tools_required": ["Multimeter"],
                    "reference_image": "/images/diagnostics/can_bus_test.png",
                    "pass_action": "next",
                    "fail_action": "resolution:res_termination"
                },
                {
                    "order": 3,
                    "instruction": "Inspect CAN bus wiring harness for damage",
                    "expected_measurement": "No visible damage, secure connections",
                    "tools_required": ["Flashlight"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_harness"
                },
                {
                    "order": 4,
                    "instruction": "Test BMS module communication independently",
                    "expected_measurement": "BMS responds to diagnostic queries",
                    "tools_required": ["Diagnostic scanner", "BMS test cable"],
                    "pass_action": "resolution:res_ecu_issue",
                    "fail_action": "resolution:res_bms_replace"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_termination",
                    "title": "CAN Termination Resistor Replacement",
                    "description": "CAN bus termination resistor faulty. Replace termination resistor.",
                    "parts_required": [{"name": "CAN Termination Resistor 120Ω", "quantity": 2, "price": 200}],
                    "labor_hours": 1.0,
                    "expected_time_minutes": 60,
                    "success_rate": 0.90
                },
                {
                    "resolution_id": "res_harness",
                    "title": "CAN Wiring Harness Repair",
                    "description": "CAN bus wiring damaged. Repair or replace harness section.",
                    "parts_required": [{"name": "CAN Bus Wiring Kit", "quantity": 1, "price": 1200}],
                    "labor_hours": 2.0,
                    "expected_time_minutes": 120,
                    "success_rate": 0.88
                },
                {
                    "resolution_id": "res_bms_replace",
                    "title": "BMS Module Replacement",
                    "description": "BMS module not communicating. Replace BMS unit.",
                    "parts_required": [{"name": "BMS Control Unit", "quantity": 1, "price": 8500}],
                    "labor_hours": 2.0,
                    "expected_time_minutes": 120,
                    "success_rate": 0.92
                },
                {
                    "resolution_id": "res_ecu_issue",
                    "title": "ECU Software Reset",
                    "description": "ECU communication state corrupted. Perform software reset.",
                    "parts_required": [],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.80
                },
                {
                    "resolution_id": "res_other_issue",
                    "title": "Alternative Diagnosis Required",
                    "description": "Issue pattern doesn't match. Perform comprehensive system scan.",
                    "parts_required": [],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.70
                }
            ]
        }
    },
    {
        "failure_id": generate_id("FC"),
        "title": "Cell Imbalance Warning",
        "subsystem_category": "battery",
        "failure_mode": "degradation",
        "symptom_text": "Reduced range, cell imbalance warning on dashboard. Some cells showing significantly different voltage.",
        "error_codes": ["E105", "CELL_IMB"],
        "root_cause": "Individual cell degradation causing voltage imbalance",
        "root_cause_details": "One or more cells in the battery pack have degraded faster than others, causing voltage imbalance during charging and discharging.",
        "keywords": ["cell", "imbalance", "voltage", "range", "degradation", "warning"],
        "status": "approved",
        "confidence_score": 0.85,
        "usage_count": 28,
        "success_count": 23,
        "effectiveness_score": 0.82,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Read individual cell voltages using BMS diagnostic tool",
                    "expected_measurement": "Cell voltage deviation > 0.1V",
                    "tools_required": ["BMS Diagnostic Tool"],
                    "reference_image": "/images/diagnostics/cell_voltage_display.png",
                    "pass_action": "next",
                    "fail_action": "resolution:res_false_alarm"
                },
                {
                    "order": 2,
                    "instruction": "Perform passive balancing cycle (full charge to 100%)",
                    "expected_measurement": "Cells balance within 0.05V after cycle",
                    "tools_required": ["Charger", "BMS Tool"],
                    "pass_action": "resolution:res_balanced",
                    "fail_action": "next"
                },
                {
                    "order": 3,
                    "instruction": "Identify specific cell modules with imbalance",
                    "expected_measurement": "Module number identified",
                    "tools_required": ["BMS Diagnostic Tool"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_full_pack"
                },
                {
                    "order": 4,
                    "instruction": "Test identified cell module under load",
                    "expected_measurement": "Voltage drop > 0.3V under 1C load",
                    "tools_required": ["Load tester", "Multimeter"],
                    "safety_notes": "Use proper PPE when handling high-voltage components",
                    "pass_action": "resolution:res_cell_replace",
                    "fail_action": "resolution:res_monitor"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_false_alarm",
                    "title": "Sensor Calibration",
                    "description": "Cell voltage sensors reading incorrectly. Recalibrate BMS.",
                    "parts_required": [],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.75
                },
                {
                    "resolution_id": "res_balanced",
                    "title": "Balancing Successful",
                    "description": "Cells balanced after full charge cycle. Monitor for recurrence.",
                    "parts_required": [],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.85
                },
                {
                    "resolution_id": "res_cell_replace",
                    "title": "Cell Module Replacement",
                    "description": "Degraded cell module identified. Replace specific module.",
                    "parts_required": [{"name": "Battery Cell Module", "quantity": 1, "price": 12000}],
                    "labor_hours": 3.0,
                    "expected_time_minutes": 180,
                    "success_rate": 0.90
                },
                {
                    "resolution_id": "res_full_pack",
                    "title": "Full Battery Pack Replacement",
                    "description": "Multiple cells degraded. Replace entire battery pack.",
                    "parts_required": [{"name": "Battery Pack Assembly", "quantity": 1, "price": 85000}],
                    "labor_hours": 4.0,
                    "expected_time_minutes": 240,
                    "success_rate": 0.98
                },
                {
                    "resolution_id": "res_monitor",
                    "title": "Monitoring Recommended",
                    "description": "Minor imbalance detected. Schedule follow-up in 30 days.",
                    "parts_required": [],
                    "labor_hours": 0.25,
                    "expected_time_minutes": 15,
                    "success_rate": 0.70
                }
            ]
        }
    }
]


# ==================== ELECTRICAL SYSTEM FAILURE CARDS ====================

ELECTRICAL_CARDS = [
    {
        "failure_id": generate_id("FC"),
        "title": "Loose Connector Issues",
        "subsystem_category": "wiring",
        "failure_mode": "intermittent",
        "symptom_text": "Intermittent power loss, flickering displays, random error codes appearing and clearing. Issues worsen on rough roads.",
        "error_codes": ["E301", "CONN_ERR"],
        "root_cause": "Loose or corroded electrical connectors",
        "root_cause_details": "Vibration and environmental factors causing connector pins to lose proper contact.",
        "keywords": ["loose", "connector", "intermittent", "flickering", "vibration", "rough road"],
        "status": "approved",
        "confidence_score": 0.88,
        "usage_count": 55,
        "success_count": 50,
        "effectiveness_score": 0.91,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Perform wiggle test on main harness connectors while monitoring for faults",
                    "expected_measurement": "Fault appears when specific connector moved",
                    "tools_required": ["Diagnostic scanner"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_other_cause"
                },
                {
                    "order": 2,
                    "instruction": "Identify affected connector and inspect for damage/corrosion",
                    "expected_measurement": "Visible corrosion or loose pins",
                    "tools_required": ["Flashlight", "Magnifier"],
                    "reference_image": "/images/diagnostics/connector_inspection.png",
                    "pass_action": "next",
                    "fail_action": "resolution:res_internal_break"
                },
                {
                    "order": 3,
                    "instruction": "Clean connector with contact cleaner and re-seat",
                    "expected_measurement": "Clean pins, proper click when connected",
                    "tools_required": ["Contact cleaner", "Compressed air"],
                    "pass_action": "resolution:res_cleaned",
                    "fail_action": "resolution:res_replace_connector"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_cleaned",
                    "title": "Connector Cleaned and Reseated",
                    "description": "Connector cleaned and properly reseated. Apply dielectric grease.",
                    "parts_required": [
                        {"name": "Contact Cleaner", "quantity": 1, "price": 250},
                        {"name": "Dielectric Grease", "quantity": 1, "price": 150}
                    ],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.85
                },
                {
                    "resolution_id": "res_replace_connector",
                    "title": "Connector Replacement",
                    "description": "Connector damaged beyond repair. Replace connector assembly.",
                    "parts_required": [{"name": "Connector Assembly Kit", "quantity": 1, "price": 800}],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.92
                },
                {
                    "resolution_id": "res_internal_break",
                    "title": "Wiring Harness Repair",
                    "description": "Internal wire break detected. Repair or replace harness section.",
                    "parts_required": [{"name": "Wiring Repair Kit", "quantity": 1, "price": 600}],
                    "labor_hours": 2.0,
                    "expected_time_minutes": 120,
                    "success_rate": 0.88
                },
                {
                    "resolution_id": "res_other_cause",
                    "title": "Further Diagnosis Required",
                    "description": "Connector test negative. Check for other intermittent sources.",
                    "parts_required": [],
                    "labor_hours": 1.0,
                    "expected_time_minutes": 60,
                    "success_rate": 0.70
                }
            ]
        }
    },
    {
        "failure_id": generate_id("FC"),
        "title": "Wiring Harness Faults",
        "subsystem_category": "wiring",
        "failure_mode": "complete_failure",
        "symptom_text": "Complete system failure, burnt smell, visible wire damage. Vehicle not responding to ignition.",
        "error_codes": ["E302", "MAIN_FUSE"],
        "root_cause": "Wiring harness damage from rodent, abrasion, or overheating",
        "root_cause_details": "Physical damage to main wiring harness causing short circuit or open circuit condition.",
        "keywords": ["wiring", "harness", "burnt", "damage", "short", "rodent", "not starting"],
        "status": "approved",
        "confidence_score": 0.90,
        "usage_count": 32,
        "success_count": 29,
        "effectiveness_score": 0.91,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Check main fuse box for blown fuses",
                    "expected_measurement": "One or more fuses blown",
                    "tools_required": ["Fuse tester"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_other_electrical"
                },
                {
                    "order": 2,
                    "instruction": "Visually inspect wiring harness for damage (look for rodent marks, abrasion)",
                    "expected_measurement": "Visible damage to insulation",
                    "tools_required": ["Flashlight", "Inspection mirror"],
                    "reference_image": "/images/diagnostics/harness_damage.png",
                    "pass_action": "next",
                    "fail_action": "resolution:res_hidden_damage"
                },
                {
                    "order": 3,
                    "instruction": "Test harness continuity in damaged section",
                    "expected_measurement": "Open circuit or short to ground",
                    "tools_required": ["Multimeter"],
                    "pass_action": "resolution:res_harness_repair",
                    "fail_action": "resolution:res_full_harness"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_harness_repair",
                    "title": "Harness Repair",
                    "description": "Repair damaged section with proper splicing and insulation.",
                    "parts_required": [
                        {"name": "Wire Splice Kit", "quantity": 1, "price": 400},
                        {"name": "Heat Shrink Tubing", "quantity": 1, "price": 150},
                        {"name": "Rodent Deterrent Tape", "quantity": 1, "price": 350}
                    ],
                    "labor_hours": 2.5,
                    "expected_time_minutes": 150,
                    "success_rate": 0.85
                },
                {
                    "resolution_id": "res_full_harness",
                    "title": "Full Harness Replacement",
                    "description": "Extensive damage. Replace complete wiring harness.",
                    "parts_required": [{"name": "Main Wiring Harness", "quantity": 1, "price": 18000}],
                    "labor_hours": 6.0,
                    "expected_time_minutes": 360,
                    "success_rate": 0.95
                },
                {
                    "resolution_id": "res_hidden_damage",
                    "title": "Trace Hidden Damage",
                    "description": "No visible damage. Use wire tracer to locate hidden break.",
                    "parts_required": [{"name": "Wire Tracer Rental", "quantity": 1, "price": 500}],
                    "labor_hours": 2.0,
                    "expected_time_minutes": 120,
                    "success_rate": 0.80
                },
                {
                    "resolution_id": "res_other_electrical",
                    "title": "Check Other Electrical Components",
                    "description": "Fuses intact. Check ECU and other control modules.",
                    "parts_required": [],
                    "labor_hours": 1.0,
                    "expected_time_minutes": 60,
                    "success_rate": 0.75
                }
            ]
        }
    },
    {
        "failure_id": generate_id("FC"),
        "title": "DC-DC Converter Failure",
        "subsystem_category": "wiring",
        "failure_mode": "complete_failure",
        "symptom_text": "12V accessories not working, warning lights on, unable to start despite high-voltage battery being charged.",
        "error_codes": ["E303", "12V_LOW", "DCDC_ERR"],
        "root_cause": "DC-DC converter not converting high voltage to 12V",
        "root_cause_details": "The DC-DC converter that powers 12V systems from the main battery pack has failed.",
        "keywords": ["dc-dc", "12v", "converter", "accessories", "lights", "not starting"],
        "status": "approved",
        "confidence_score": 0.91,
        "usage_count": 25,
        "success_count": 23,
        "effectiveness_score": 0.92,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Measure 12V auxiliary battery voltage",
                    "expected_measurement": "Below 11V indicates charging issue",
                    "tools_required": ["Multimeter"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_12v_ok"
                },
                {
                    "order": 2,
                    "instruction": "Check DC-DC converter input voltage (HV side)",
                    "expected_measurement": "Should match main battery voltage (300-400V typical)",
                    "tools_required": ["HV-rated Multimeter"],
                    "safety_notes": "Use HV-rated equipment. Follow HV safety procedures.",
                    "pass_action": "next",
                    "fail_action": "resolution:res_hv_issue"
                },
                {
                    "order": 3,
                    "instruction": "Check DC-DC converter output with vehicle ON",
                    "expected_measurement": "Should output 13.5-14.5V",
                    "tools_required": ["Multimeter"],
                    "pass_action": "resolution:res_12v_battery",
                    "fail_action": "resolution:res_dcdc_replace"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_12v_ok",
                    "title": "12V System Normal",
                    "description": "12V voltage normal. Issue may be elsewhere.",
                    "parts_required": [],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.70
                },
                {
                    "resolution_id": "res_hv_issue",
                    "title": "High Voltage Supply Issue",
                    "description": "No HV reaching DC-DC. Check HV fuse and connections.",
                    "parts_required": [{"name": "HV Fuse", "quantity": 1, "price": 800}],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.88
                },
                {
                    "resolution_id": "res_dcdc_replace",
                    "title": "DC-DC Converter Replacement",
                    "description": "DC-DC converter faulty. Replace unit.",
                    "parts_required": [{"name": "DC-DC Converter Unit", "quantity": 1, "price": 12000}],
                    "labor_hours": 2.0,
                    "expected_time_minutes": 120,
                    "success_rate": 0.94
                },
                {
                    "resolution_id": "res_12v_battery",
                    "title": "12V Auxiliary Battery Replacement",
                    "description": "DC-DC working but 12V battery not holding charge.",
                    "parts_required": [{"name": "12V Auxiliary Battery", "quantity": 1, "price": 4500}],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.95
                }
            ]
        }
    },
    {
        "failure_id": generate_id("FC"),
        "title": "Low Voltage System Failure",
        "subsystem_category": "wiring",
        "failure_mode": "degradation",
        "symptom_text": "Dim lights, slow accessories, warning messages about low voltage. May progress to complete failure.",
        "error_codes": ["E304", "LV_WARN"],
        "root_cause": "12V auxiliary battery degradation or charging system fault",
        "root_cause_details": "The 12V auxiliary battery has degraded or is not being properly charged by the DC-DC converter.",
        "keywords": ["low voltage", "dim lights", "slow", "auxiliary", "12v", "degradation"],
        "status": "approved",
        "confidence_score": 0.86,
        "usage_count": 42,
        "success_count": 37,
        "effectiveness_score": 0.88,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Measure 12V battery voltage with vehicle OFF",
                    "expected_measurement": "Should be 12.4V or higher when rested",
                    "tools_required": ["Multimeter"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_charge_test"
                },
                {
                    "order": 2,
                    "instruction": "Load test 12V battery",
                    "expected_measurement": "Maintains >9.6V under 100A load",
                    "tools_required": ["Battery load tester"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_replace_12v"
                },
                {
                    "order": 3,
                    "instruction": "Check charging voltage with vehicle running",
                    "expected_measurement": "13.8-14.5V at battery terminals",
                    "tools_required": ["Multimeter"],
                    "pass_action": "resolution:res_parasitic_draw",
                    "fail_action": "resolution:res_dcdc_check"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_replace_12v",
                    "title": "12V Battery Replacement",
                    "description": "12V battery failed load test. Replace battery.",
                    "parts_required": [{"name": "12V Auxiliary Battery", "quantity": 1, "price": 4500}],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.92
                },
                {
                    "resolution_id": "res_charge_test",
                    "title": "Charge and Retest",
                    "description": "Battery voltage low. Charge fully and retest.",
                    "parts_required": [],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.75
                },
                {
                    "resolution_id": "res_dcdc_check",
                    "title": "DC-DC Converter Check",
                    "description": "Not charging properly. Check DC-DC converter.",
                    "parts_required": [],
                    "labor_hours": 1.0,
                    "expected_time_minutes": 60,
                    "success_rate": 0.85
                },
                {
                    "resolution_id": "res_parasitic_draw",
                    "title": "Parasitic Draw Test",
                    "description": "Battery and charging OK. Check for parasitic current draw.",
                    "parts_required": [],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.80
                }
            ]
        }
    }
]


# ==================== CONTROLLER/SOFTWARE FAILURE CARDS ====================

CONTROLLER_CARDS = [
    {
        "failure_id": generate_id("FC"),
        "title": "Controller Communication Error",
        "subsystem_category": "controller",
        "failure_mode": "no_response",
        "symptom_text": "Multiple warning lights, vehicle in limp mode or not responding. Diagnostic tool cannot connect to ECU.",
        "error_codes": ["E401", "ECU_COMM", "TIMEOUT"],
        "root_cause": "ECU communication failure or ECU malfunction",
        "root_cause_details": "Vehicle controller not responding to diagnostic commands. Could be power supply, communication line, or ECU itself.",
        "keywords": ["controller", "ecu", "communication", "timeout", "limp mode", "warning lights"],
        "status": "approved",
        "confidence_score": 0.88,
        "usage_count": 35,
        "success_count": 30,
        "effectiveness_score": 0.86,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Check ECU power supply fuse",
                    "expected_measurement": "Fuse intact with continuity",
                    "tools_required": ["Multimeter", "Fuse tester"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_fuse_replace"
                },
                {
                    "order": 2,
                    "instruction": "Check ECU ground connection",
                    "expected_measurement": "Less than 0.5 ohm to chassis",
                    "tools_required": ["Multimeter"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_ground_repair"
                },
                {
                    "order": 3,
                    "instruction": "Check OBD diagnostic port pins",
                    "expected_measurement": "12V on pin 16, ground on pins 4,5",
                    "tools_required": ["Multimeter", "OBD pinout diagram"],
                    "reference_image": "/images/diagnostics/obd_pinout.png",
                    "pass_action": "next",
                    "fail_action": "resolution:res_obd_repair"
                },
                {
                    "order": 4,
                    "instruction": "Attempt ECU reset by disconnecting 12V battery for 5 minutes",
                    "expected_measurement": "ECU responds after reconnection",
                    "tools_required": ["10mm wrench"],
                    "pass_action": "resolution:res_reset_success",
                    "fail_action": "resolution:res_ecu_replace"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_fuse_replace",
                    "title": "ECU Fuse Replacement",
                    "description": "ECU fuse blown. Replace fuse and check for underlying cause.",
                    "parts_required": [{"name": "ECU Fuse 15A", "quantity": 2, "price": 100}],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.85
                },
                {
                    "resolution_id": "res_ground_repair",
                    "title": "ECU Ground Repair",
                    "description": "Poor ground connection. Clean and secure ground point.",
                    "parts_required": [{"name": "Ground Strap", "quantity": 1, "price": 200}],
                    "labor_hours": 1.0,
                    "expected_time_minutes": 60,
                    "success_rate": 0.90
                },
                {
                    "resolution_id": "res_obd_repair",
                    "title": "OBD Port Repair",
                    "description": "OBD port damaged. Repair or replace OBD connector.",
                    "parts_required": [{"name": "OBD Port Assembly", "quantity": 1, "price": 1200}],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.88
                },
                {
                    "resolution_id": "res_reset_success",
                    "title": "ECU Reset Successful",
                    "description": "ECU recovered after power reset. Monitor for recurrence.",
                    "parts_required": [],
                    "labor_hours": 0.25,
                    "expected_time_minutes": 15,
                    "success_rate": 0.75
                },
                {
                    "resolution_id": "res_ecu_replace",
                    "title": "ECU Replacement",
                    "description": "ECU not responding. Replace ECU and reprogram.",
                    "parts_required": [{"name": "Vehicle ECU", "quantity": 1, "price": 25000}],
                    "labor_hours": 3.0,
                    "expected_time_minutes": 180,
                    "success_rate": 0.95
                }
            ]
        }
    },
    {
        "failure_id": generate_id("FC"),
        "title": "Firmware Lock State",
        "subsystem_category": "controller",
        "failure_mode": "complete_failure",
        "symptom_text": "Vehicle completely locked, showing firmware update failed message. Cannot boot normally.",
        "error_codes": ["E402", "FW_LOCK", "BOOT_FAIL"],
        "root_cause": "Interrupted or corrupted firmware update",
        "root_cause_details": "Firmware update was interrupted (power loss, communication error) leaving ECU in locked state.",
        "keywords": ["firmware", "lock", "update", "boot", "fail", "corrupted", "brick"],
        "status": "approved",
        "confidence_score": 0.92,
        "usage_count": 18,
        "success_count": 16,
        "effectiveness_score": 0.89,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Attempt recovery mode boot (hold brake + power button)",
                    "expected_measurement": "Recovery menu appears",
                    "tools_required": [],
                    "reference_image": "/images/diagnostics/recovery_mode.png",
                    "pass_action": "next",
                    "fail_action": "resolution:res_jtag_recovery"
                },
                {
                    "order": 2,
                    "instruction": "Connect to recovery mode and check firmware status",
                    "expected_measurement": "Shows corrupted or incomplete firmware",
                    "tools_required": ["Diagnostic laptop", "OEM software"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_factory_support"
                },
                {
                    "order": 3,
                    "instruction": "Initiate firmware recovery/reinstall from OEM server",
                    "expected_measurement": "Firmware downloads and installs successfully",
                    "tools_required": ["Diagnostic laptop", "Internet connection"],
                    "pass_action": "resolution:res_fw_recovered",
                    "fail_action": "resolution:res_ecu_replace"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_fw_recovered",
                    "title": "Firmware Recovery Successful",
                    "description": "Firmware reinstalled successfully. Vehicle should boot normally.",
                    "parts_required": [],
                    "labor_hours": 1.0,
                    "expected_time_minutes": 60,
                    "success_rate": 0.90
                },
                {
                    "resolution_id": "res_jtag_recovery",
                    "title": "JTAG Recovery Required",
                    "description": "Standard recovery failed. Use JTAG interface for low-level recovery.",
                    "parts_required": [{"name": "JTAG Recovery Service", "quantity": 1, "price": 3000}],
                    "labor_hours": 3.0,
                    "expected_time_minutes": 180,
                    "success_rate": 0.85
                },
                {
                    "resolution_id": "res_factory_support",
                    "title": "Factory Support Required",
                    "description": "Contact factory for specialized recovery procedure.",
                    "parts_required": [],
                    "labor_hours": 1.0,
                    "expected_time_minutes": 60,
                    "success_rate": 0.80
                },
                {
                    "resolution_id": "res_ecu_replace",
                    "title": "ECU Replacement",
                    "description": "ECU unrecoverable. Replace with new programmed unit.",
                    "parts_required": [{"name": "Vehicle ECU (Programmed)", "quantity": 1, "price": 28000}],
                    "labor_hours": 2.5,
                    "expected_time_minutes": 150,
                    "success_rate": 0.98
                }
            ]
        }
    },
    {
        "failure_id": generate_id("FC"),
        "title": "Throttle Signal Mismatch",
        "subsystem_category": "controller",
        "failure_mode": "erratic_behavior",
        "symptom_text": "Erratic acceleration, vehicle not responding to throttle correctly. May surge or have dead spots.",
        "error_codes": ["E403", "TPS_ERR", "THROTTLE_MISMATCH"],
        "root_cause": "Throttle position sensor calibration or hardware failure",
        "root_cause_details": "Throttle position sensors not reporting consistent values to controller.",
        "keywords": ["throttle", "accelerator", "surge", "erratic", "dead spot", "tps", "acceleration"],
        "status": "approved",
        "confidence_score": 0.89,
        "usage_count": 40,
        "success_count": 36,
        "effectiveness_score": 0.90,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Read TPS1 and TPS2 values at rest position",
                    "expected_measurement": "Both sensors show 0-5% throttle",
                    "tools_required": ["Diagnostic scanner"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_tps_calibrate"
                },
                {
                    "order": 2,
                    "instruction": "Slowly press throttle and compare TPS1/TPS2 tracking",
                    "expected_measurement": "Both values increase proportionally",
                    "tools_required": ["Diagnostic scanner"],
                    "reference_image": "/images/diagnostics/tps_graph.png",
                    "pass_action": "next",
                    "fail_action": "resolution:res_tps_replace"
                },
                {
                    "order": 3,
                    "instruction": "Check throttle pedal mechanism for binding",
                    "expected_measurement": "Smooth pedal travel, no sticking",
                    "tools_required": ["Flashlight"],
                    "pass_action": "resolution:res_controller_check",
                    "fail_action": "resolution:res_pedal_replace"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_tps_calibrate",
                    "title": "TPS Calibration",
                    "description": "Throttle sensors need recalibration. Perform TPS relearn procedure.",
                    "parts_required": [],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.85
                },
                {
                    "resolution_id": "res_tps_replace",
                    "title": "TPS Sensor Replacement",
                    "description": "Throttle position sensor faulty. Replace TPS assembly.",
                    "parts_required": [{"name": "TPS Assembly", "quantity": 1, "price": 3500}],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.92
                },
                {
                    "resolution_id": "res_pedal_replace",
                    "title": "Throttle Pedal Replacement",
                    "description": "Pedal mechanism faulty. Replace complete pedal assembly.",
                    "parts_required": [{"name": "Throttle Pedal Assembly", "quantity": 1, "price": 4500}],
                    "labor_hours": 1.0,
                    "expected_time_minutes": 60,
                    "success_rate": 0.95
                },
                {
                    "resolution_id": "res_controller_check",
                    "title": "Controller Software Check",
                    "description": "Sensors and pedal OK. Check for controller software update.",
                    "parts_required": [],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.80
                }
            ]
        }
    }
]


# ==================== MOTOR/MECHANICAL FAILURE CARDS ====================

MOTOR_CARDS = [
    {
        "failure_id": generate_id("FC"),
        "title": "Hall Sensor Failure",
        "subsystem_category": "motor",
        "failure_mode": "erratic_behavior",
        "symptom_text": "Jerky motor operation, motor not starting smoothly, position errors on diagnostic. May work intermittently.",
        "error_codes": ["E501", "HALL_ERR", "MOTOR_POS"],
        "root_cause": "Hall effect sensor failure in motor",
        "root_cause_details": "One or more hall sensors used for motor position feedback have failed or become intermittent.",
        "keywords": ["hall", "sensor", "motor", "jerky", "position", "intermittent", "starting"],
        "status": "approved",
        "confidence_score": 0.90,
        "usage_count": 48,
        "success_count": 44,
        "effectiveness_score": 0.92,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Read hall sensor status from motor controller",
                    "expected_measurement": "All 3 hall signals present and switching",
                    "tools_required": ["Diagnostic scanner", "Oscilloscope (optional)"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_hall_identify"
                },
                {
                    "order": 2,
                    "instruction": "Manually rotate motor and observe hall signal changes",
                    "expected_measurement": "Clean transitions on all sensors",
                    "tools_required": ["Diagnostic scanner"],
                    "reference_image": "/images/diagnostics/hall_signals.png",
                    "pass_action": "resolution:res_wiring_check",
                    "fail_action": "resolution:res_hall_replace"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_hall_identify",
                    "title": "Identify Failed Hall Sensor",
                    "description": "One or more hall sensors not reporting. Identify specific failed sensor.",
                    "parts_required": [],
                    "labor_hours": 0.5,
                    "expected_time_minutes": 30,
                    "success_rate": 0.95
                },
                {
                    "resolution_id": "res_hall_replace",
                    "title": "Hall Sensor Replacement",
                    "description": "Hall sensor(s) faulty. Replace motor hall sensor assembly.",
                    "parts_required": [{"name": "Hall Sensor Kit (3pcs)", "quantity": 1, "price": 2500}],
                    "labor_hours": 3.0,
                    "expected_time_minutes": 180,
                    "success_rate": 0.90
                },
                {
                    "resolution_id": "res_wiring_check",
                    "title": "Hall Sensor Wiring Check",
                    "description": "Signals OK but intermittent. Check wiring connections.",
                    "parts_required": [{"name": "Hall Sensor Connector", "quantity": 1, "price": 400}],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.85
                }
            ]
        }
    },
    {
        "failure_id": generate_id("FC"),
        "title": "Motor Overheating",
        "subsystem_category": "motor",
        "failure_mode": "overheating",
        "symptom_text": "Power reduction warning, motor temperature high, vehicle limiting speed or power. Occurs especially in hot weather or uphill.",
        "error_codes": ["E502", "MOT_TEMP", "DERATING"],
        "root_cause": "Motor cooling system issue or overload condition",
        "root_cause_details": "Motor temperature exceeding safe limits due to cooling failure or sustained high load operation.",
        "keywords": ["motor", "overheating", "temperature", "derating", "power reduction", "cooling"],
        "status": "approved",
        "confidence_score": 0.87,
        "usage_count": 35,
        "success_count": 30,
        "effectiveness_score": 0.86,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Check motor cooling fan operation",
                    "expected_measurement": "Fan spins when motor temp > 60°C",
                    "tools_required": ["IR thermometer"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_fan_replace"
                },
                {
                    "order": 2,
                    "instruction": "Inspect motor cooling fins/housing for debris",
                    "expected_measurement": "Clean air passages",
                    "tools_required": ["Compressed air", "Brush"],
                    "reference_image": "/images/diagnostics/motor_cooling.png",
                    "pass_action": "next",
                    "fail_action": "resolution:res_clean_motor"
                },
                {
                    "order": 3,
                    "instruction": "Check motor phase current balance under load",
                    "expected_measurement": "All 3 phases within 5% of each other",
                    "tools_required": ["Clamp ammeter", "Diagnostic tool"],
                    "pass_action": "resolution:res_usage_advice",
                    "fail_action": "resolution:res_motor_service"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_fan_replace",
                    "title": "Cooling Fan Replacement",
                    "description": "Motor cooling fan not operating. Replace fan assembly.",
                    "parts_required": [{"name": "Motor Cooling Fan", "quantity": 1, "price": 2800}],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.92
                },
                {
                    "resolution_id": "res_clean_motor",
                    "title": "Motor Cleaning",
                    "description": "Cooling blocked by debris. Clean motor and cooling passages.",
                    "parts_required": [{"name": "Motor Cleaning Service", "quantity": 1, "price": 500}],
                    "labor_hours": 1.0,
                    "expected_time_minutes": 60,
                    "success_rate": 0.88
                },
                {
                    "resolution_id": "res_motor_service",
                    "title": "Motor Service/Rebuild",
                    "description": "Phase imbalance indicates motor issue. Service or rebuild motor.",
                    "parts_required": [{"name": "Motor Service Kit", "quantity": 1, "price": 5000}],
                    "labor_hours": 4.0,
                    "expected_time_minutes": 240,
                    "success_rate": 0.85
                },
                {
                    "resolution_id": "res_usage_advice",
                    "title": "Usage Recommendations",
                    "description": "Motor OK but usage pattern causing overheating. Advise on proper usage.",
                    "parts_required": [],
                    "labor_hours": 0.25,
                    "expected_time_minutes": 15,
                    "success_rate": 0.75
                }
            ]
        }
    },
    {
        "failure_id": generate_id("FC"),
        "title": "Sudden Torque Loss",
        "subsystem_category": "motor",
        "failure_mode": "complete_failure",
        "symptom_text": "Complete loss of motor power while riding. Vehicle coasts to stop. May restart after cooling.",
        "error_codes": ["E503", "TORQUE_LOSS", "MOT_FAULT"],
        "root_cause": "Motor phase failure or controller protection activation",
        "root_cause_details": "One or more motor phases have failed, or controller has cut power due to detected fault.",
        "keywords": ["torque", "loss", "power", "coast", "sudden", "motor", "phase"],
        "status": "approved",
        "confidence_score": 0.91,
        "usage_count": 22,
        "success_count": 20,
        "effectiveness_score": 0.91,
        "decision_tree": {
            "steps": [
                {
                    "order": 1,
                    "instruction": "Read stored fault codes from controller",
                    "expected_measurement": "Fault code present indicating cause",
                    "tools_required": ["Diagnostic scanner"],
                    "pass_action": "next",
                    "fail_action": "resolution:res_no_code"
                },
                {
                    "order": 2,
                    "instruction": "Check motor phase resistance (U-V, V-W, W-U)",
                    "expected_measurement": "All phases equal within 10%",
                    "tools_required": ["Multimeter"],
                    "reference_image": "/images/diagnostics/phase_test.png",
                    "safety_notes": "Ensure controller is OFF and disconnected",
                    "pass_action": "next",
                    "fail_action": "resolution:res_motor_replace"
                },
                {
                    "order": 3,
                    "instruction": "Check motor phase cables for damage",
                    "expected_measurement": "No visible damage, secure connections",
                    "tools_required": ["Flashlight"],
                    "pass_action": "resolution:res_controller_test",
                    "fail_action": "resolution:res_phase_cable"
                }
            ],
            "resolutions": [
                {
                    "resolution_id": "res_motor_replace",
                    "title": "Motor Replacement",
                    "description": "Motor phase winding failure detected. Replace motor.",
                    "parts_required": [{"name": "Hub Motor Assembly", "quantity": 1, "price": 18000}],
                    "labor_hours": 3.0,
                    "expected_time_minutes": 180,
                    "success_rate": 0.95
                },
                {
                    "resolution_id": "res_phase_cable",
                    "title": "Phase Cable Replacement",
                    "description": "Motor phase cable damaged. Replace cable assembly.",
                    "parts_required": [{"name": "Motor Phase Cable Set", "quantity": 1, "price": 3500}],
                    "labor_hours": 2.0,
                    "expected_time_minutes": 120,
                    "success_rate": 0.90
                },
                {
                    "resolution_id": "res_controller_test",
                    "title": "Controller Testing",
                    "description": "Motor OK. Test motor controller output stages.",
                    "parts_required": [],
                    "labor_hours": 1.5,
                    "expected_time_minutes": 90,
                    "success_rate": 0.85
                },
                {
                    "resolution_id": "res_no_code",
                    "title": "Manual Diagnosis Required",
                    "description": "No fault code stored. Perform comprehensive motor/controller test.",
                    "parts_required": [],
                    "labor_hours": 2.0,
                    "expected_time_minutes": 120,
                    "success_rate": 0.80
                }
            ]
        }
    }
]


# ==================== SEED FUNCTION ====================

async def seed_failure_cards_and_trees(db):
    """Seed all failure cards with their decision trees.
    Sprint 3B-SEED: also generates embeddings for each card."""
    
    all_cards = BATTERY_CARDS + ELECTRICAL_CARDS + CONTROLLER_CARDS + MOTOR_CARDS
    
    cards_inserted = 0
    cards_skipped = 0
    trees_inserted = 0
    embeddings_generated = 0
    
    # Initialize embedding service for card embedding generation
    embedding_manager = None
    try:
        from services.efi_embedding_service import EFIEmbeddingManager
        embedding_manager = EFIEmbeddingManager(db)
    except Exception as e:
        import logging
        logging.getLogger("efi_seed").warning(f"Embedding service unavailable: {e}")
    
    for card_data in all_cards:
        # Extract decision tree data
        tree_data = card_data.pop("decision_tree", None)
        
        # Add common fields
        card_data["source_type"] = "seeded"
        card_data["is_seed_data"] = True
        card_data["organization_id"] = None  # Shared brain — no org
        card_data["ticket_id"] = f"seed-{card_data['failure_id']}"  # Unique ticket_id for index compat
        card_data["card_id"] = card_data["failure_id"]  # Alias for unique index on card_id
        card_data["status"] = card_data.get("status", "approved")
        card_data["created_at"] = datetime.now(timezone.utc).isoformat()
        card_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        card_data["first_detected_at"] = datetime.now(timezone.utc).isoformat()
        
        # Check if card already exists (by title or failure_id)
        existing = await db.failure_cards.find_one(
            {"$or": [
                {"title": card_data.get("title")},
                {"failure_id": card_data.get("failure_id")}
            ]}
        )
        if existing:
            card_data["failure_id"] = existing.get("failure_id") or existing.get("card_id")
            cards_skipped += 1
        else:
            # Insert card
            await db.failure_cards.insert_one(card_data)
            cards_inserted += 1
            
            # Sprint 3B-03: Generate embedding for seed card
            if embedding_manager:
                try:
                    card_text = " ".join(filter(None, [
                        card_data.get("title", ""),
                        card_data.get("symptom_text", ""),
                        card_data.get("root_cause", ""),
                        card_data.get("subsystem_category", ""),
                    ])).strip()
                    if card_text:
                        emb_result = await embedding_manager.generate_complaint_embedding(card_text)
                        if emb_result and emb_result.get("embedding"):
                            await db.failure_cards.update_one(
                                {"failure_id": card_data["failure_id"]},
                                {"$set": {
                                    "embedding_vector": emb_result["embedding"],
                                    "embedding_generated_at": datetime.now(timezone.utc).isoformat()
                                }}
                            )
                            embeddings_generated += 1
                except Exception as emb_err:
                    import logging
                    logging.getLogger("efi_seed").warning(
                        f"Embedding failed for {card_data.get('title')}: {emb_err}"
                    )
        
        # Create decision tree
        if tree_data:
            tree_exists = await db.efi_decision_trees.find_one({"failure_card_id": card_data["failure_id"]})
            if not tree_exists:
                tree_doc = {
                    "tree_id": f"tree_{uuid.uuid4().hex[:8]}",
                    "failure_card_id": card_data["failure_id"],
                    "version": 1,
                    "steps": [],
                    "resolutions": [],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Process steps
                for i, step in enumerate(tree_data.get("steps", [])):
                    step_id = f"step_{uuid.uuid4().hex[:8]}"
                    step["step_id"] = step_id
                    step["order"] = step.get("order", i + 1)
                    tree_doc["steps"].append(step)
                
                # Set entry step
                if tree_doc["steps"]:
                    tree_doc["entry_step_id"] = tree_doc["steps"][0]["step_id"]
                
                # Process resolutions
                for res in tree_data.get("resolutions", []):
                    if "resolution_id" not in res:
                        res["resolution_id"] = f"res_{uuid.uuid4().hex[:8]}"
                    res["labor_rate"] = res.get("labor_rate", 500)
                    tree_doc["resolutions"].append(res)
                
                await db.efi_decision_trees.insert_one(tree_doc)
                trees_inserted += 1
    
    return {
        "cards_inserted": cards_inserted,
        "cards_skipped": cards_skipped,
        "trees_inserted": trees_inserted,
        "embeddings_generated": embeddings_generated,
        "total_cards": len(all_cards)
    }


# ==================== SEED KNOWLEDGE ARTICLES (Sprint 6B-02) ====================

async def seed_knowledge_articles(db):
    """
    Create knowledge articles from seeded failure cards.
    These are global (organization_id=None, scope=global)
    because they come from shared seed data.
    """
    seed_cards = await db.failure_cards.find(
        {"is_seed_data": True},
        {"_id": 0}
    ).to_list(100)

    inserted = 0
    skipped = 0

    for card in seed_cards:
        card_id = card.get("card_id") or card.get("failure_id")
        if not card_id:
            skipped += 1
            continue

        existing = await db.knowledge_articles.find_one(
            {"source_id": card_id},
            {"_id": 0, "knowledge_id": 1}
        )
        if existing:
            skipped += 1
            continue

        article = {
            "knowledge_id": f"KB-SEED-{card_id}",
            "organization_id": None,
            "scope": "global",
            "knowledge_type": "repair_procedure",
            "title": card.get("title") or card.get("issue_title", ""),
            "summary": card.get("symptom_text") or card.get("description", ""),
            "content": "\n\n".join(filter(None, [
                f"**Root Cause:** {card.get('root_cause', '')}",
                f"**Diagnosis Steps:** {chr(10).join(str(s.get('instruction', s)) for s in card.get('diagnosis_steps', []))}" if card.get("diagnosis_steps") else None,
                f"**Resolution Steps:** {chr(10).join(str(s) for s in card.get('resolution_steps', []))}" if card.get("resolution_steps") else None,
                f"**Root Cause Details:** {card.get('root_cause_details', '')}" if card.get("root_cause_details") else None,
            ])),
            "symptoms": card.get("symptoms") or card.get("symptom_cluster", []),
            "dtc_codes": card.get("dtc_codes") or card.get("error_codes", []),
            "vehicle_category": card.get("vehicle_category", "2W"),
            "subsystem": card.get("subsystem_category") or card.get("subsystem", "unknown"),
            "confidence_score": card.get("confidence_score", 0.7),
            "approval_status": "approved",
            "source_type": "seed_data",
            "source_id": card_id,
            "created_by": "system_seed",
            "is_seed_data": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        await db.knowledge_articles.insert_one(article)
        inserted += 1

    return {"inserted": inserted, "skipped": skipped}


# Run seeding if called directly
if __name__ == "__main__":
    import motor.motor_asyncio
    import os
    
    async def main():
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.environ.get("DB_NAME", "battwheels")
        
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        result = await seed_failure_cards_and_trees(db)
        print(f"Seeding complete: {result}")
        
        client.close()
    
    asyncio.run(main())
