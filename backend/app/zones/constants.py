# backend/app/zones/constants.py
ZONE_NAMES: list[str] = [
    "inbound_dock_a", "inbound_dock_b", "staging_area_1", "staging_area_2",
    "aisle_1", "aisle_2", "aisle_3", "aisle_4", "aisle_5",
    "charging_bay_1", "charging_bay_2", "charging_bay_3",
    "outbound_dock_a", "outbound_dock_b",
    "quality_check", "returns_area", "overflow_1", "overflow_2",
    "maintenance_bay", "dispatch_hub",
]
assert len(ZONE_NAMES) == 20, "Exactly 20 zones required (ZONE-03)"
