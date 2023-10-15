from symphonyGPT.performers.performer import Performer


class Generator(Performer):
    def __init__(self):
        super().__init__()
        self.set_type("generator")