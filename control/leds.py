class LedController:
    def __init__(self, arduino, logger=None): self.arduino=arduino; self.logger=logger; self.states={'RED':False,'BLUE':False,'WHITE':False}
    def toggle(self,name):
        self.states[name]=not self.states[name]; value='ON' if self.states[name] else 'OFF'; self.arduino.send(f'{name}:{value}')
        if self.logger: self.logger.log(f'{name} LED -> {value}')
