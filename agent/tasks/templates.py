# tasks/templates.py — Pre-built Task Workflows for Boss
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class TaskTemplate:
    name: str
    description: str
    required_fields: List[str]
    optional_fields: List[str] = field(default_factory=list)
    confirmation_required: bool = True
    steps: List[str] = field(default_factory=list)
    
    def get_missing(self, collected: Dict[str, Any]) -> List[str]:
        return [f for f in self.required_fields if f not in collected or collected[f] is None]
    
    def is_complete(self, collected: Dict[str, Any]) -> bool:
        return all(f in collected and collected[f] is not None for f in self.required_fields)


# ─── Task Registry ─────────────────────────────────────

TASK_REGISTRY = {
    "book_restaurant": TaskTemplate(
        name="book_restaurant",
        description="Book a table at a restaurant",
        required_fields=["restaurant", "time", "people"],
        optional_fields=["date", "special_requests"],
        confirmation_required=True,
        steps=["collect_info", "check_availability", "hold_slot", "confirm"]
    ),
    
    "check_order": TaskTemplate(
        name="check_order",
        description="Check the status of an order",
        required_fields=["order_id"],
        optional_fields=[],
        confirmation_required=False,
        steps=["collect_info", "lookup_order", "report_status"]
    ),
    
    "plan_trip": TaskTemplate(
        name="plan_trip",
        description="Plan a trip with hotel and activities",
        required_fields=["destination", "dates", "travelers"],
        optional_fields=["budget", "preferences"],
        confirmation_required=True,
        steps=["collect_info", "search_hotels", "search_activities", "present_options", "confirm"]
    ),
    
    "file_complaint": TaskTemplate(
        name="file_complaint",
        description="File a support complaint or request",
        required_fields=["issue_type", "description"],
        optional_fields=["order_id", "contact_email"],
        confirmation_required=True,
        steps=["collect_info", "categorize", "submit"]
    ),
    
    "open_and_summarize": TaskTemplate(
        name="open_and_summarize",
        description="Open a file or folder and summarize its contents",
        required_fields=["target_path"],
        optional_fields=["file_type_filter"],
        confirmation_required=False,
        steps=["collect_info", "access_target", "summarize"]
    ),
}
