class Command:
    def __init__(self):
        self.prefix    = "k"
        self.separator = " "

    def __call__(self, string):
        splited = string.split(self.separator)
        prefix = splited[0].lower()
        if prefix[:len(self.prefix)] == self.prefix:
            arg = [prefix[len(self.prefix):]]
            if not arg[0]: arg = []
            args = arg + splited[1:]
            return args[0], args[1:]
        return False, []

