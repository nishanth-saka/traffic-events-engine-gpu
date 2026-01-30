def detect_vehicles(frame):
    """
    Returns list of vehicles with crops.
    Replace internals with YOLO later.
    """

    h, w = frame.shape[:2]

    # TEMP: fake single vehicle in center
    crop = frame[h//4: 3*h//4, w//4: 3*w//4]

    return [{
        "bbox": [w//4, h//4, 3*w//4, 3*h//4],
        "class": "vehicle",
        "confidence": 0.9,
        "crop": crop,
    }]
