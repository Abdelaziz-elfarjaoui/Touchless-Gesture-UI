class MotorController:
    def __init__(self, arduino, logger=None):
        self.arduino=arduino; self.logger=logger; self.speed=0; self.last_sent=-1
    def set_speed(self, speed):
        speed=max(0,min(100,int(speed))); self.speed=speed
        if speed != self.last_sent:
            self.last_sent=speed; self.arduino.send(f'SPEED:{speed}')
            if self.logger: self.logger.log(f'Motor speed -> {speed}%')
    def safety_stop(self):
        self.speed=0; self.last_sent=0; self.arduino.send('SPEED:0')
        if self.logger: self.logger.log('SAFETY STOP - hand lost')
