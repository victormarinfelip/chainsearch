


class NoAbiTemplateError(Exception):

    def __init__(self, name:str = ""):
        """
        raised when a model can't find the correct abi json

        :param name: Model's name
        """
        self.name = name

    def __str__(self):
        return "Model {} can't find abi json".format(self.name)
