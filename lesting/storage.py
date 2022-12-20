class Storage:
    attributes = {}

    def __init__(self):
        self.values = {}

    def __call__(self, key):
        return type(self.__class__.__name__, (object,), {**{ "key": key }, **{ attr: self.create_property(key, attr, default) for attr, default in self.attributes.items() }})()

    def handler(self, key, value):
        return

    def create_property(self, key, attr, default):
        def function_get(node):
            return self.values.get(key, {}).get(attr, default)
        def function_set(node, value):
            obj = self.values.setdefault(key, {})
            if value != obj.get(attr, default):
                obj[attr] = value
                self.handler(key, obj)
        return property(function_get, function_set)