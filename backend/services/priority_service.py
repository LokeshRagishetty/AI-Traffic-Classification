def assign_priority(traffic_class: str) -> str:
    """
    Deterministically assigns a priority based on the traffic class.
    This does not contain any ML, networking, or scheduling logic.
    """
    mapping = {
        "Gaming": "Critical",
        "VoIP": "Critical",
        "Video Streaming": "High",
        "Web Browsing": "Medium",
        "File Transfer": "Low"
    }
    
    priority = mapping.get(traffic_class)
    if not priority:
        raise ValueError(f"Unknown traffic class: {traffic_class}")
        
    return priority
