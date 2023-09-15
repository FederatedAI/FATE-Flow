class FateFlowError(Exception):
    code = None
    message = 'Unknown Fate Flow Error'

    def __init__(self, message=None, **kwargs):
        self.code = self.code
        self.message = str(message) if message is not None else self.message
        suffix = ""
        if kwargs:
            for k, v in kwargs.items():
                if v is not None and not callable(v):
                    if suffix:
                        suffix += ","
                    suffix += f"{k}[{v}]"
        if suffix:
            self.message += f": {suffix}"
        super().__init__(self.code, self.message)
