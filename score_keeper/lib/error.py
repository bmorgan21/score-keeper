class ActionError(ValueError):
    def __init__(self, msg, loc=None, type=None):
        super().__init__(msg)

        self.loc = loc or ""
        self.type = f"action_error.{type}" if type else "action_error"


class ForbiddenActionError(ActionError):
    def __init__(self, loc=None, type="forbidden"):
        super().__init__("Action Denied", loc=loc, type=type)
