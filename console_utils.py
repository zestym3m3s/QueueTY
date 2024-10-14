class ConsoleStream:
    def __init__(self, append_func):
        self.append_func = append_func

    def write(self, message):
        if message and not message.isspace():
            try:
                self.append_func(message)
            except Exception:
                # Avoid recursion by not using print inside the custom write method
                pass

    def flush(self):
        pass  # No need to implement flush for this use case
