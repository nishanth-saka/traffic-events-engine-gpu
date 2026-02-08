def detect_wrong_direction(pairs, allowed_vector):
    events = []
    for prev, curr in pairs:
        dx = curr.cx - prev.cx
        dy = curr.cy - prev.cy

        if violates(dx, dy, allowed_vector):
            events.append({
                "type": "wrong_direction",
                "confidence": 0.8
            })
    return events
