"""
Battwheels OS - EFI Master Fault Tree Import Engine
Structured ingestion pipeline for importing EV Failure Intelligence from Excel

Features:
- Excel parsing with section detection
- Field mapping to FAILURE_CARD schema
- Data normalization and validation
- Deduplication with similarity matching
- Version control
- Batch processing with progress tracking
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from enum import Enum
import uuid
import re
import hashlib
import logging

logger = logging.getLogger(__name__)


class ImportStatus(str, Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    VALIDATED = "validated"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ValidationStatus(str, Enum):
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"


class VehicleCategory(str, Enum):
    TWO_WHEELER = "2w"
    THREE_WHEELER_PASSENGER = "3w_passenger"
    THREE_WHEELER_CARGO = "3w_cargo"
    FOUR_WHEELER_PASSENGER = "4w_passenger"
    COMMERCIAL_BUS = "commercial_bus"


class SubsystemType(str, Enum):
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    ELECTRONICS = "electronics"
    SOFTWARE = "software"


# ==================== DATA MODELS ====================

class ParsedFaultTreeRow(BaseModel):
    """Single parsed row from Excel"""
    row_number: int
    sr_no: Optional[str] = None
    complaint_description: str
    root_causes: List[str] = []
    diagnostic_steps: List[str] = []
    fault_tree_logic: Optional[str] = None
    resolution_steps: List[str] = []
    prevention_tips: List[str] = []
    
    # Derived fields
    vehicle_category: Optional[VehicleCategory] = None
    subsystem_type: Optional[SubsystemType] = None
    section_header: Optional[str] = None
    
    # Validation
    validation_status: ValidationStatus = ValidationStatus.VALID
    validation_errors: List[str] = []
    validation_warnings: List[str] = []


class ImportJob(BaseModel):
    """Import job tracking"""
    job_id: str = Field(default_factory=lambda: f"imp_{uuid.uuid4().hex[:12]}")
    filename: str
    file_url: Optional[str] = None
    
    # Status
    status: ImportStatus = ImportStatus.PENDING
    progress_percent: float = 0.0
    
    # Counts
    total_rows: int = 0
    valid_rows: int = 0
    error_rows: int = 0
    warning_rows: int = 0
    imported_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    
    # Results
    created_card_ids: List[str] = []
    updated_card_ids: List[str] = []
    error_details: List[Dict[str, Any]] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # User
    created_by: Optional[str] = None


class ImportPreview(BaseModel):
    """Preview of parsed data before import"""
    job_id: str
    filename: str
    total_rows: int
    valid_rows: int
    error_rows: int
    warning_rows: int
    
    # Section breakdown
    sections: List[Dict[str, Any]] = []
    
    # Sample data
    sample_valid: List[Dict[str, Any]] = []
    sample_errors: List[Dict[str, Any]] = []
    
    # Deduplication preview
    potential_duplicates: int = 0
    new_cards: int = 0
    updates: int = 0


# ==================== PARSING ENGINE ====================

class FaultTreeParser:
    """
    Parses Excel fault tree data and maps to FAILURE_CARD schema
    """
    
    # Section header patterns
    SECTION_PATTERNS = [
        (r"2W EV.*Mechanical", VehicleCategory.TWO_WHEELER, SubsystemType.MECHANICAL),
        (r"2W EV.*Electrical", VehicleCategory.TWO_WHEELER, SubsystemType.ELECTRICAL),
        (r"2W EV.*Electronics", VehicleCategory.TWO_WHEELER, SubsystemType.ELECTRONICS),
        (r"2W EV.*Software", VehicleCategory.TWO_WHEELER, SubsystemType.SOFTWARE),
        (r"3W Passenger.*Mechanical", VehicleCategory.THREE_WHEELER_PASSENGER, SubsystemType.MECHANICAL),
        (r"3W Passenger.*Electrical", VehicleCategory.THREE_WHEELER_PASSENGER, SubsystemType.ELECTRICAL),
        (r"3W Passenger.*Electronics", VehicleCategory.THREE_WHEELER_PASSENGER, SubsystemType.ELECTRONICS),
        (r"3W Cargo.*Mechanical", VehicleCategory.THREE_WHEELER_CARGO, SubsystemType.MECHANICAL),
        (r"3W Cargo.*Electrical", VehicleCategory.THREE_WHEELER_CARGO, SubsystemType.ELECTRICAL),
        (r"3W Cargo.*Electronics", VehicleCategory.THREE_WHEELER_CARGO, SubsystemType.ELECTRONICS),
        (r"4W Passenger.*Mechanical", VehicleCategory.FOUR_WHEELER_PASSENGER, SubsystemType.MECHANICAL),
        (r"4W Passenger.*Electrical", VehicleCategory.FOUR_WHEELER_PASSENGER, SubsystemType.ELECTRICAL),
        (r"Passenger Commercial|Bus EV", VehicleCategory.COMMERCIAL_BUS, SubsystemType.MECHANICAL),
        (r"Mechanical.*\d+–\d+", None, SubsystemType.MECHANICAL),
        (r"Electrical.*\d+–\d+", None, SubsystemType.ELECTRICAL),
        (r"Electronics.*\d+–\d+", None, SubsystemType.ELECTRONICS),
    ]
    
    def __init__(self):
        self.current_vehicle_category: Optional[VehicleCategory] = VehicleCategory.TWO_WHEELER
        self.current_subsystem_type: Optional[SubsystemType] = SubsystemType.MECHANICAL
        self.current_section_header: Optional[str] = None
    
    def parse_excel(self, file_path: str) -> List[ParsedFaultTreeRow]:
        """Parse entire Excel file"""
        import pandas as pd
        
        df = pd.read_excel(file_path, sheet_name=0, header=1)
        df.columns = [
            'Sr_No', 'Complaint_Description', 'Root_Causes', 
            'Diagnostic_Steps', 'Fault_Tree_Logic', 
            'Resolution_Steps', 'Prevention_Tips'
        ]
        
        parsed_rows = []
        
        for idx, row in df.iterrows():
            parsed = self._parse_row(idx, row)
            if parsed:
                parsed_rows.append(parsed)
        
        return parsed_rows
    
    def _parse_row(self, idx: int, row) -> Optional[ParsedFaultTreeRow]:
        """Parse a single row"""
        import pandas as pd
        
        sr_no = row.get('Sr_No')
        complaint = row.get('Complaint_Description')
        root_causes = row.get('Root_Causes')
        
        # Skip completely empty rows
        if pd.isna(complaint) or str(complaint).strip() == '' or str(complaint) == 'nan':
            return None
        
        complaint = str(complaint).strip()
        
        # Check if this is a section header
        if pd.isna(root_causes) or str(root_causes).strip() == '' or str(root_causes) == 'nan':
            self._update_section_context(complaint)
            return None
        
        # Parse as data row
        parsed = ParsedFaultTreeRow(
            row_number=idx + 2,  # Excel row number (1-indexed + header)
            sr_no=str(sr_no) if not pd.isna(sr_no) else None,
            complaint_description=self._clean_complaint(complaint),
            root_causes=self._parse_numbered_list(str(root_causes)),
            diagnostic_steps=self._parse_arrow_list(str(row.get('Diagnostic_Steps', ''))),
            fault_tree_logic=self._clean_text(str(row.get('Fault_Tree_Logic', ''))),
            resolution_steps=self._parse_slash_list(str(row.get('Resolution_Steps', ''))),
            prevention_tips=self._parse_comma_list(str(row.get('Prevention_Tips', ''))),
            vehicle_category=self.current_vehicle_category,
            subsystem_type=self.current_subsystem_type,
            section_header=self.current_section_header
        )
        
        return parsed
    
    def _update_section_context(self, text: str):
        """Update current section context based on header"""
        self.current_section_header = text
        
        for pattern, vehicle, subsystem in self.SECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if vehicle:
                    self.current_vehicle_category = vehicle
                if subsystem:
                    self.current_subsystem_type = subsystem
                break
    
    def _clean_complaint(self, text: str) -> str:
        """Clean complaint description"""
        # Remove leading numbers like "45. "
        text = re.sub(r'^\d+\.\s*', '', text)
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Normalize text formatting"""
        if not text or text == 'nan':
            return ""
        text = text.strip()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _parse_numbered_list(self, text: str) -> List[str]:
        """Parse numbered list like '1. Item 2. Item'"""
        if not text or text == 'nan':
            return []
        
        # Split by number pattern
        items = re.split(r'\d+\.\s*', text)
        items = [self._clean_text(item) for item in items if item.strip()]
        return items
    
    def _parse_arrow_list(self, text: str) -> List[str]:
        """Parse arrow-separated list like 'Step1 → Step2 → Step3'"""
        if not text or text == 'nan':
            return []
        
        # Split by arrow or similar separators
        items = re.split(r'[→➔➜→>]|->|\|\|', text)
        items = [self._clean_text(item) for item in items if item.strip()]
        return items
    
    def _parse_slash_list(self, text: str) -> List[str]:
        """Parse slash-separated list like 'Option1 / Option2'"""
        if not text or text == 'nan':
            return []
        
        items = re.split(r'\s*/\s*', text)
        items = [self._clean_text(item) for item in items if item.strip()]
        return items
    
    def _parse_comma_list(self, text: str) -> List[str]:
        """Parse comma-separated list"""
        if not text or text == 'nan':
            return []
        
        items = re.split(r',\s*', text)
        items = [self._clean_text(item) for item in items if item.strip()]
        return items


# ==================== VALIDATION ENGINE ====================

class FaultTreeValidator:
    """Validates parsed fault tree data"""
    
    def validate_row(self, row: ParsedFaultTreeRow) -> ParsedFaultTreeRow:
        """Validate a single parsed row"""
        errors = []
        warnings = []
        
        # Required fields
        if not row.complaint_description:
            errors.append("Missing complaint description")
        
        if not row.root_causes:
            errors.append("Missing root causes")
        
        if not row.diagnostic_steps:
            warnings.append("Missing diagnostic steps")
        
        if not row.resolution_steps:
            warnings.append("Missing resolution steps")
        
        # Quality checks
        if row.complaint_description and len(row.complaint_description) < 5:
            warnings.append("Complaint description too short")
        
        if len(row.root_causes) == 1 and len(row.root_causes[0]) > 200:
            warnings.append("Root causes may not be properly separated")
        
        # Update status
        row.validation_errors = errors
        row.validation_warnings = warnings
        
        if errors:
            row.validation_status = ValidationStatus.ERROR
        elif warnings:
            row.validation_status = ValidationStatus.WARNING
        else:
            row.validation_status = ValidationStatus.VALID
        
        return row
    
    def validate_all(self, rows: List[ParsedFaultTreeRow]) -> List[ParsedFaultTreeRow]:
        """Validate all rows"""
        return [self.validate_row(row) for row in rows]


# ==================== MAPPING ENGINE ====================

class FailureCardMapper:
    """Maps parsed fault tree data to FAILURE_CARD schema"""
    
    SUBSYSTEM_MAP = {
        SubsystemType.MECHANICAL: "mechanical",
        SubsystemType.ELECTRICAL: "wiring",
        SubsystemType.ELECTRONICS: "controller",
        SubsystemType.SOFTWARE: "software",
    }
    
    def map_to_failure_card(self, row: ParsedFaultTreeRow) -> Dict[str, Any]:
        """Map a single row to failure card format"""
        failure_id = f"fc_{uuid.uuid4().hex[:12]}"
        
        # Build failure signature
        signature = self._build_signature(row)
        signature_hash = self._compute_hash(signature)
        
        # Build diagnostic tree
        diagnostic_tree = self._build_diagnostic_tree(row.diagnostic_steps)
        
        # Parse fault tree logic
        fault_tree_logic = self._parse_fault_tree_logic(row.fault_tree_logic)
        
        # Map subsystem
        subsystem = self._map_subsystem(row)
        
        # Build keywords
        keywords = self._extract_keywords(row)
        
        # Initial confidence (OEM input gets higher baseline)
        initial_confidence = 0.7
        
        card = {
            "failure_id": failure_id,
            "title": row.complaint_description,
            "description": self._build_description(row),
            "subsystem_category": subsystem,
            "failure_mode": self._infer_failure_mode(row.complaint_description),
            
            # Signature
            "failure_signature": signature,
            "signature_hash": signature_hash,
            
            # Symptoms
            "symptom_text": row.complaint_description,
            "symptom_codes": [],
            "error_codes": [],
            
            # Root cause
            "root_cause": row.root_causes[0] if row.root_causes else "Under investigation",
            "root_cause_details": "\n".join(row.root_causes[1:]) if len(row.root_causes) > 1 else None,
            "secondary_causes": row.root_causes[1:] if len(row.root_causes) > 1 else [],
            "probable_causes": row.root_causes,
            
            # Diagnostic tree
            "diagnostic_tree": diagnostic_tree,
            
            # Resolution
            "resolution_steps": self._build_resolution_steps(row.resolution_steps),
            "resolution_summary": " / ".join(row.resolution_steps),
            
            # Prevention
            "prevention_guidelines": row.prevention_tips,
            
            # Fault tree logic
            "fault_tree_logic": fault_tree_logic,
            
            # Vehicle compatibility
            "vehicle_models": self._build_vehicle_models(row.vehicle_category),
            
            # Keywords
            "keywords": keywords,
            "tags": [row.vehicle_category.value if row.vehicle_category else "2w"],
            
            # Provenance
            "source_type": "legacy_import",
            "source_import_ref": f"Battwheels Master Fault Tree - Row {row.row_number}",
            "source_sr_no": row.sr_no,
            
            # Intelligence
            "confidence_score": initial_confidence,
            "confidence_level": "medium",
            "confidence_history": [{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "previous_score": 0.0,
                "new_score": initial_confidence,
                "change_reason": "import_creation",
                "notes": "Imported from Battwheels Master Fault Tree"
            }],
            
            # Status
            "status": "approved",  # Pre-validated OEM data
            "version": 1,
            
            # Timestamps
            "created_at": datetime.now(timezone.utc).isoformat(),
            "first_detected_at": datetime.now(timezone.utc).isoformat(),
        }
        
        return card
    
    def _build_signature(self, row: ParsedFaultTreeRow) -> Dict[str, Any]:
        """Build failure signature from parsed data"""
        return {
            "primary_symptoms": self._extract_symptom_keywords(row.complaint_description),
            "error_codes": [],
            "subsystem": self._map_subsystem(row),
            "failure_mode": self._infer_failure_mode(row.complaint_description),
            "vehicle_category": row.vehicle_category.value if row.vehicle_category else "2w",
        }
    
    def _compute_hash(self, signature: Dict[str, Any]) -> str:
        """Compute signature hash"""
        components = [
            ",".join(sorted(signature.get("primary_symptoms", []))),
            signature.get("subsystem", ""),
            signature.get("failure_mode", ""),
            signature.get("vehicle_category", ""),
        ]
        hash_input = "|".join(components).lower()
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _build_diagnostic_tree(self, steps: List[str]) -> Optional[Dict[str, Any]]:
        """Build diagnostic tree structure"""
        if not steps:
            return None
        
        nodes = []
        for i, step in enumerate(steps):
            node = {
                "node_id": f"dn_{uuid.uuid4().hex[:6]}",
                "step_number": i + 1,
                "question": f"Step {i + 1} complete?",
                "check_action": step,
                "expected_outcome": "Proceed to next step",
                "tools_required": [],
                "duration_minutes": 5,
                "if_yes": None,
                "if_no": None,
            }
            nodes.append(node)
        
        # Link nodes
        for i in range(len(nodes) - 1):
            nodes[i]["if_yes"] = nodes[i + 1]["node_id"]
        
        return {
            "tree_id": f"dt_{uuid.uuid4().hex[:8]}",
            "root_node_id": nodes[0]["node_id"] if nodes else None,
            "nodes": nodes,
            "total_paths": 1,
            "avg_path_length": len(nodes),
        }
    
    def _parse_fault_tree_logic(self, logic_text: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parse fault tree logic into structured format"""
        if not logic_text:
            return None
        
        # Parse patterns like "Top Event: X → OR (A, B, C)"
        result = {
            "raw": logic_text,
            "top_event": None,
            "gate_type": None,
            "branches": [],
        }
        
        # Extract top event
        top_match = re.search(r'Top Event:\s*([^→]+)', logic_text, re.IGNORECASE)
        if top_match:
            result["top_event"] = top_match.group(1).strip()
        
        # Extract gate type
        if "OR" in logic_text.upper():
            result["gate_type"] = "OR"
        elif "AND" in logic_text.upper():
            result["gate_type"] = "AND"
        
        # Extract branches
        branch_match = re.search(r'\((.*?)\)', logic_text)
        if branch_match:
            branches = [b.strip() for b in branch_match.group(1).split(',')]
            result["branches"] = branches
        
        return result
    
    def _map_subsystem(self, row: ParsedFaultTreeRow) -> str:
        """Map to subsystem category"""
        if row.subsystem_type:
            return self.SUBSYSTEM_MAP.get(row.subsystem_type, "other")
        
        # Infer from complaint
        complaint_lower = row.complaint_description.lower()
        if any(w in complaint_lower for w in ["battery", "charging", "soc"]):
            return "battery"
        elif any(w in complaint_lower for w in ["motor", "power", "torque"]):
            return "motor"
        elif any(w in complaint_lower for w in ["brake", "wheel", "suspension", "fork"]):
            return "brakes"
        elif any(w in complaint_lower for w in ["display", "screen", "cluster"]):
            return "display"
        elif any(w in complaint_lower for w in ["controller", "bms", "mcu"]):
            return "controller"
        elif any(w in complaint_lower for w in ["wire", "cable", "fuse", "relay"]):
            return "wiring"
        
        return "other"
    
    def _infer_failure_mode(self, complaint: str) -> str:
        """Infer failure mode from complaint"""
        complaint_lower = complaint.lower()
        
        if any(w in complaint_lower for w in ["no ", "dead", "won't", "not working", "failed"]):
            return "complete_failure"
        elif any(w in complaint_lower for w in ["intermittent", "sometimes", "occasional"]):
            return "intermittent"
        elif any(w in complaint_lower for w in ["slow", "reduced", "low", "weak"]):
            return "degradation"
        elif any(w in complaint_lower for w in ["noise", "sound", "squeal"]):
            return "noise"
        elif any(w in complaint_lower for w in ["hot", "heat", "overheating"]):
            return "overheating"
        elif any(w in complaint_lower for w in ["vibration", "shake", "wobble"]):
            return "vibration"
        
        return "erratic_behavior"
    
    def _build_resolution_steps(self, steps: List[str]) -> List[Dict[str, Any]]:
        """Build resolution steps structure"""
        return [
            {
                "step_number": i + 1,
                "action": step,
                "details": None,
                "tools_required": [],
                "parts_required": [],
                "duration_minutes": 15,
                "skill_level": "intermediate",
            }
            for i, step in enumerate(steps)
        ]
    
    def _build_vehicle_models(self, category: Optional[VehicleCategory]) -> List[Dict[str, str]]:
        """Build vehicle models based on category"""
        if not category:
            return []
        
        vehicle_map = {
            VehicleCategory.TWO_WHEELER: [
                {"make": "Ather", "model": "450X"},
                {"make": "Ola", "model": "S1 Pro"},
                {"make": "TVS", "model": "iQube"},
            ],
            VehicleCategory.THREE_WHEELER_PASSENGER: [
                {"make": "Mahindra", "model": "Treo"},
                {"make": "Piaggio", "model": "Ape E-City"},
            ],
            VehicleCategory.THREE_WHEELER_CARGO: [
                {"make": "Mahindra", "model": "Treo Zor"},
                {"make": "Euler", "model": "HiLoad"},
            ],
            VehicleCategory.FOUR_WHEELER_PASSENGER: [
                {"make": "Tata", "model": "Nexon EV"},
                {"make": "MG", "model": "ZS EV"},
            ],
            VehicleCategory.COMMERCIAL_BUS: [
                {"make": "Tata", "model": "Ultra E-Bus"},
            ],
        }
        
        return vehicle_map.get(category, [])
    
    def _extract_keywords(self, row: ParsedFaultTreeRow) -> List[str]:
        """Extract keywords from all fields"""
        keywords = set()
        
        # From complaint
        keywords.update(self._extract_symptom_keywords(row.complaint_description))
        
        # From root causes
        for cause in row.root_causes:
            keywords.update(self._extract_symptom_keywords(cause))
        
        # Add category tags
        if row.vehicle_category:
            keywords.add(row.vehicle_category.value)
        if row.subsystem_type:
            keywords.add(row.subsystem_type.value)
        
        return list(keywords)[:30]
    
    def _extract_symptom_keywords(self, text: str) -> List[str]:
        """Extract symptom-related keywords"""
        if not text:
            return []
        
        # Normalize
        text = text.lower()
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                     'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                     'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through'}
        
        words = re.findall(r'[a-z]+', text)
        keywords = [w for w in words if len(w) > 2 and w not in stopwords]
        
        return keywords[:10]
    
    def _build_description(self, row: ParsedFaultTreeRow) -> str:
        """Build full description"""
        parts = [
            f"Complaint: {row.complaint_description}",
            f"\nRoot Causes (by probability):",
        ]
        for i, cause in enumerate(row.root_causes, 1):
            parts.append(f"  {i}. {cause}")
        
        if row.fault_tree_logic:
            parts.append(f"\nFault Tree: {row.fault_tree_logic}")
        
        return "\n".join(parts)


# ==================== DEDUPLICATION ENGINE ====================

class DeduplicationEngine:
    """Handles deduplication of failure cards"""
    
    def __init__(self, db):
        self.db = db
    
    async def find_duplicates(self, card: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potential duplicate cards"""
        duplicates = []
        
        # Check by signature hash (fastest)
        sig_match = await self.db.failure_cards.find_one(
            {"signature_hash": card.get("signature_hash")},
            {"_id": 0, "failure_id": 1, "title": 1, "version": 1}
        )
        if sig_match:
            duplicates.append({**sig_match, "match_type": "signature_exact"})
            return duplicates  # Exact match found, no need for more checks
        
        # Check by similar title using regex (fallback if text index unavailable)
        try:
            title_matches = await self.db.failure_cards.find(
                {"$text": {"$search": card.get("title", "")}},
                {"_id": 0, "failure_id": 1, "title": 1, "version": 1, "score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(3).to_list(3)
            
            for match in title_matches:
                if match["failure_id"] not in [d["failure_id"] for d in duplicates]:
                    duplicates.append({**match, "match_type": "title_similarity"})
        except Exception as e:
            # Fallback to regex if text index not available
            logger.warning(f"Text search failed, using regex fallback: {e}")
            title = card.get("title", "")
            if title:
                # Simple keyword extraction
                words = [w for w in title.lower().split() if len(w) > 3][:3]
                if words:
                    regex_pattern = "|".join(words)
                    title_matches = await self.db.failure_cards.find(
                        {"title": {"$regex": regex_pattern, "$options": "i"}},
                        {"_id": 0, "failure_id": 1, "title": 1, "version": 1}
                    ).limit(3).to_list(3)
                    
                    for match in title_matches:
                        if match["failure_id"] not in [d["failure_id"] for d in duplicates]:
                            duplicates.append({**match, "match_type": "title_similarity"})
        
        return duplicates
    
    async def should_update_existing(self, new_card: Dict[str, Any], existing: Dict[str, Any]) -> bool:
        """Determine if existing card should be updated"""
        # Update if signature matches exactly
        if existing.get("match_type") == "signature_exact":
            return True
        
        # Don't update if score is low
        if existing.get("score", 0) < 5:
            return False
        
        return False


# ==================== IMPORT SERVICE ====================

class FaultTreeImportService:
    """Main import service orchestrating the pipeline"""
    
    def __init__(self, db):
        self.db = db
        self.parser = FaultTreeParser()
        self.validator = FaultTreeValidator()
        self.mapper = FailureCardMapper()
        self.deduplicator = DeduplicationEngine(db)
    
    async def create_import_job(self, filename: str, file_url: str, user_id: str) -> ImportJob:
        """Create a new import job"""
        job = ImportJob(
            filename=filename,
            file_url=file_url,
            created_by=user_id
        )
        
        doc = job.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await self.db.import_jobs.insert_one(doc)
        
        return job
    
    async def parse_and_preview(self, job_id: str, file_path: str) -> ImportPreview:
        """Parse file and generate preview"""
        # Update job status
        await self.db.import_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": ImportStatus.VALIDATING.value}}
        )
        
        # Parse
        parsed_rows = self.parser.parse_excel(file_path)
        
        # Validate
        validated_rows = self.validator.validate_all(parsed_rows)
        
        # Store parsed data
        for row in validated_rows:
            doc = row.model_dump()
            doc['job_id'] = job_id
            await self.db.parsed_rows.insert_one(doc)
        
        # Count statistics
        valid_count = sum(1 for r in validated_rows if r.validation_status == ValidationStatus.VALID)
        error_count = sum(1 for r in validated_rows if r.validation_status == ValidationStatus.ERROR)
        warning_count = sum(1 for r in validated_rows if r.validation_status == ValidationStatus.WARNING)
        
        # Group by section
        sections = {}
        for row in validated_rows:
            key = f"{row.vehicle_category.value if row.vehicle_category else 'unknown'}_{row.subsystem_type.value if row.subsystem_type else 'unknown'}"
            if key not in sections:
                sections[key] = {
                    "vehicle_category": row.vehicle_category.value if row.vehicle_category else None,
                    "subsystem_type": row.subsystem_type.value if row.subsystem_type else None,
                    "count": 0
                }
            sections[key]["count"] += 1
        
        # Check duplicates
        potential_duplicates = 0
        for row in validated_rows[:20]:  # Sample check
            card = self.mapper.map_to_failure_card(row)
            dupes = await self.deduplicator.find_duplicates(card)
            if dupes:
                potential_duplicates += 1
        
        # Update job
        await self.db.import_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": ImportStatus.VALIDATED.value,
                "total_rows": len(validated_rows),
                "valid_rows": valid_count,
                "error_rows": error_count,
                "warning_rows": warning_count,
            }}
        )
        
        # Build preview
        preview = ImportPreview(
            job_id=job_id,
            filename="",
            total_rows=len(validated_rows),
            valid_rows=valid_count,
            error_rows=error_count,
            warning_rows=warning_count,
            sections=list(sections.values()),
            sample_valid=[
                r.model_dump() for r in validated_rows 
                if r.validation_status == ValidationStatus.VALID
            ][:5],
            sample_errors=[
                r.model_dump() for r in validated_rows 
                if r.validation_status == ValidationStatus.ERROR
            ][:5],
            potential_duplicates=potential_duplicates,
            new_cards=valid_count - potential_duplicates,
            updates=potential_duplicates,
        )
        
        return preview
    
    async def execute_import(
        self, 
        job_id: str, 
        skip_duplicates: bool = True,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """Execute the import"""
        # Update status
        await self.db.import_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": ImportStatus.IMPORTING.value,
                "started_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Get parsed rows
        # H-01: hard cap, remove in Sprint 3 when cursor pagination implemented
        rows = await self.db.parsed_rows.find(
            {"job_id": job_id, "validation_status": {"$ne": ValidationStatus.ERROR.value}}
        ).to_list(1000)
        
        total = len(rows)
        created = 0
        updated = 0
        skipped = 0
        errors = []
        created_ids = []
        updated_ids = []
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = rows[i:i + batch_size]
            
            for row_doc in batch:
                try:
                    row = ParsedFaultTreeRow(**row_doc)
                    card = self.mapper.map_to_failure_card(row)
                    
                    # Check duplicates
                    dupes = await self.deduplicator.find_duplicates(card)
                    
                    if dupes and skip_duplicates:
                        # Update existing
                        existing = dupes[0]
                        if await self.deduplicator.should_update_existing(card, existing):
                            # Increment version and update
                            await self.db.failure_cards.update_one(
                                {"failure_id": existing["failure_id"]},
                                {
                                    "$inc": {"version": 1},
                                    "$set": {
                                        "updated_at": datetime.now(timezone.utc).isoformat(),
                                        "source_import_ref": card["source_import_ref"],
                                    },
                                    "$push": {
                                        "version_history": {
                                            "version": existing.get("version", 1),
                                            "updated_at": datetime.now(timezone.utc).isoformat(),
                                            "source": "fault_tree_import",
                                            "job_id": job_id
                                        }
                                    }
                                }
                            )
                            updated += 1
                            updated_ids.append(existing["failure_id"])
                        else:
                            skipped += 1
                    else:
                        # Create new
                        await self.db.failure_cards.insert_one(card)
                        created += 1
                        created_ids.append(card["failure_id"])
                
                except Exception as e:
                    errors.append({
                        "row_number": row_doc.get("row_number"),
                        "error": str(e)
                    })
            
            # Update progress
            progress = ((i + len(batch)) / total) * 100
            await self.db.import_jobs.update_one(
                {"job_id": job_id},
                {"$set": {"progress_percent": progress}}
            )
        
        # Final update
        final_status = ImportStatus.COMPLETED if not errors else ImportStatus.PARTIAL
        await self.db.import_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": final_status.value,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "imported_count": created,
                "updated_count": updated,
                "skipped_count": skipped,
                "created_card_ids": created_ids,
                "updated_card_ids": updated_ids,
                "error_details": errors,
                "progress_percent": 100.0
            }}
        )
        
        return {
            "status": final_status.value,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "errors": len(errors),
            "created_ids": created_ids[:10],
            "error_details": errors[:10]
        }
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get import job status"""
        job = await self.db.import_jobs.find_one({"job_id": job_id}, {"_id": 0})
        return job
    
    async def list_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent import jobs"""
        jobs = await self.db.import_jobs.find(
            {}, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        return jobs
