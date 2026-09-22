import pytest
from services.priority_service import assign_priority

def test_priority_mappings():
    assert assign_priority("Gaming") == "Critical"
    assert assign_priority("VoIP") == "Critical"
    assert assign_priority("Video Streaming") == "High"
    assert assign_priority("Web Browsing") == "Medium"
    assert assign_priority("File Transfer") == "Low"

def test_unknown_traffic_class():
    with pytest.raises(ValueError) as excinfo:
        assign_priority("Unknown Class")
    assert "Unknown traffic class: Unknown Class" in str(excinfo.value)

def test_priority_is_deterministic():
    # Calling it multiple times should always yield the exact same result
    for _ in range(10):
        assert assign_priority("Gaming") == "Critical"
