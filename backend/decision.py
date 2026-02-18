def decision_logic(humidity: float, last_state: bool) -> bool:
    if humidity < 55 and not last_state:
        return True
    if humidity > 65 and last_state:
        return False
    return last_state