"""
FHIR (Fast Healthcare Interoperability Resources) utilities for the Medical AI Agent.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class FHIRUtils:
    """Manages FHIR-compatible medical records and data."""
    
    def __init__(self, data_file: str = "data/sample_fhir_records.json"):
        self.data_file = data_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load FHIR data from JSON file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded FHIR data from {self.data_file}")
                return data
            else:
                logger.warning(f"FHIR data file not found: {self.data_file}")
                return {"patients": [], "appointments": [], "doctors": [], "faqs": []}
        except Exception as e:
            logger.error(f"Failed to load FHIR data: {e}")
            return {"patients": [], "appointments": [], "doctors": [], "faqs": []}
    
    def _save_data(self):
        """Save FHIR data to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
            logger.info(f"Saved FHIR data to {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to save FHIR data: {e}")
    
    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Get patient record by ID."""
        for patient in self.data.get("patients", []):
            if patient.get("id") == patient_id:
                return patient
        return None
    
    def search_patients(self, query: str) -> List[Dict]:
        """Search patients by name or other criteria."""
        results = []
        query_lower = query.lower()
        
        for patient in self.data.get("patients", []):
            if (query_lower in patient.get("name", "").lower() or
                query_lower in patient.get("id", "").lower()):
                results.append(patient)
        
        return results
    
    def get_patient_appointments(self, patient_id: str) -> List[Dict]:
        """Get all appointments for a patient."""
        appointments = []
        for appt in self.data.get("appointments", []):
            if appt.get("patient_id") == patient_id:
                appointments.append(appt)
        
        return sorted(appointments, key=lambda x: x.get("date", ""))
    
    def get_patient_medical_history(self, patient_id: str) -> List[Dict]:
        """Get medical history for a patient."""
        patient = self.get_patient(patient_id)
        if patient:
            return patient.get("medical_history", [])
        return []
    
    def get_patient_medications(self, patient_id: str) -> List[Dict]:
        """Get current medications for a patient."""
        patient = self.get_patient(patient_id)
        if patient:
            return patient.get("medications", [])
        return []
    
    def get_patient_allergies(self, patient_id: str) -> List[str]:
        """Get allergies for a patient."""
        patient = self.get_patient(patient_id)
        if patient:
            return patient.get("allergies", [])
        return []
    
    def add_appointment(self, appointment_data: Dict) -> str:
        """Add a new appointment."""
        # Generate appointment ID
        existing_ids = [appt.get("id", "") for appt in self.data.get("appointments", [])]
        new_id = f"appt-{len(existing_ids) + 1:03d}"
        
        appointment_data["id"] = new_id
        appointment_data["status"] = appointment_data.get("status", "scheduled")
        
        self.data.setdefault("appointments", []).append(appointment_data)
        self._save_data()
        
        logger.info(f"Added appointment {new_id} for patient {appointment_data.get('patient_id')}")
        return new_id
    
    def update_appointment(self, appointment_id: str, updates: Dict) -> bool:
        """Update an existing appointment."""
        for appt in self.data.get("appointments", []):
            if appt.get("id") == appointment_id:
                appt.update(updates)
                self._save_data()
                logger.info(f"Updated appointment {appointment_id}")
                return True
        
        logger.warning(f"Appointment {appointment_id} not found for update")
        return False
    
    def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment."""
        return self.update_appointment(appointment_id, {"status": "cancelled"})
    
    def get_available_doctors(self, specialty: str = None) -> List[Dict]:
        """Get available doctors, optionally filtered by specialty."""
        doctors = self.data.get("doctors", [])
        
        if specialty:
            doctors = [d for d in doctors if specialty.lower() in d.get("specialty", "").lower()]
        
        return doctors
    
    def get_doctor_availability(self, doctor_id: str, date: str = None) -> List[str]:
        """Get available time slots for a doctor on a specific date."""
        for doctor in self.data.get("doctors", []):
            if doctor.get("id") == doctor_id or doctor.get("name") == doctor_id:
                # Return available slots (in a real system, this would filter by date)
                return doctor.get("available_slots", ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"])
        return []
    
    def add_medical_record_entry(self, patient_id: str, entry_type: str, data: Dict) -> bool:
        """Add a new medical record entry for a patient."""
        patient = self.get_patient(patient_id)
        if not patient:
            logger.warning(f"Patient {patient_id} not found")
            return False
        
        # Add timestamp
        data["timestamp"] = datetime.now().isoformat()
        
        # Add to appropriate section
        if entry_type == "condition":
            patient.setdefault("medical_history", []).append(data)
        elif entry_type == "medication":
            patient.setdefault("medications", []).append(data)
        elif entry_type == "allergy":
            patient.setdefault("allergies", []).append(data.get("allergen", ""))
        else:
            # Generic entry
            patient.setdefault("additional_records", []).append({
                "type": entry_type,
                "data": data
            })
        
        self._save_data()
        logger.info(f"Added {entry_type} record for patient {patient_id}")
        return True
    
    def get_faqs(self) -> List[Dict]:
        """Get all FAQ entries."""
        return self.data.get("faqs", [])
    
    def search_faqs(self, query: str) -> List[Dict]:
        """Search FAQs by question or answer content."""
        results = []
        query_lower = query.lower()
        
        for faq in self.get_faqs():
            if (query_lower in faq.get("question", "").lower() or
                query_lower in faq.get("answer", "").lower()):
                results.append(faq)
        
        return results
    
    def get_emergency_keywords(self) -> List[str]:
        """Get list of emergency keywords."""
        return self.data.get("emergency_keywords", [])
    
    def to_fhir_patient(self, patient_data: Dict) -> Dict:
        """Convert internal patient data to FHIR Patient resource format."""
        fhir_patient = {
            "resourceType": "Patient",
            "id": patient_data.get("id"),
            "name": [
                {
                    "use": "official",
                    "text": patient_data.get("name")
                }
            ],
            "gender": patient_data.get("gender"),
            "birthDate": self._calculate_birth_date(patient_data.get("age")),
            "telecom": []
        }
        
        # Add contact information
        contact = patient_data.get("contact", {})
        if contact.get("phone"):
            fhir_patient["telecom"].append({
                "system": "phone",
                "value": contact["phone"],
                "use": "home"
            })
        
        if contact.get("email"):
            fhir_patient["telecom"].append({
                "system": "email",
                "value": contact["email"]
            })
        
        return fhir_patient
    
    def _calculate_birth_date(self, age: int) -> str:
        """Calculate approximate birth date from age."""
        if age:
            current_year = datetime.now().year
            birth_year = current_year - age
            return f"{birth_year}-01-01"  # Approximate birth date
        return None

# Global FHIR manager instance
fhir_manager = FHIRUtils()

def get_patient_info(patient_id: str) -> Optional[Dict]:
    """Get patient information."""
    return fhir_manager.get_patient(patient_id)

def search_patients(query: str) -> List[Dict]:
    """Search for patients."""
    return fhir_manager.search_patients(query)

def get_patient_appointments(patient_id: str) -> List[Dict]:
    """Get patient appointments."""
    return fhir_manager.get_patient_appointments(patient_id)

def get_patient_medical_history(patient_id: str) -> List[Dict]:
    """Get patient medical history."""
    return fhir_manager.get_patient_medical_history(patient_id)

def get_available_doctors() -> List[Dict]:
    """Get list of available doctors."""
    return fhir_manager.get_doctors()

def get_doctor_availability(doctor_name: str, date: str) -> List[str]:
    """Get available time slots for a doctor on a specific date."""
    return fhir_manager.get_doctor_availability(doctor_name, date)

def get_patient_medications(patient_id: str) -> List[Dict]:
    """Get patient medications."""
    return fhir_manager.get_patient_medications(patient_id)

def get_patient_allergies(patient_id: str) -> List[str]:
    """Get patient allergies."""
    return fhir_manager.get_patient_allergies(patient_id)

def book_appointment(patient_id: str, doctor: str, date: str, time: str, appointment_type: str = "consultation") -> str:
    """Book a new appointment."""
    appointment_data = {
        "patient_id": patient_id,
        "doctor": doctor,
        "date": date,
        "time": time,
        "type": appointment_type,
        "status": "scheduled"
    }
    return fhir_manager.add_appointment(appointment_data)
