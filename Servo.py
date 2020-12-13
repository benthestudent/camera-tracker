from multiprocessing import Queue
class Servo:
    def __init__(self, upper_limit, lower_limit):
            self.upper_limit = upper_limit
            self.lower_limit = lower_limit
            self.current_pos = Queue()  # Servo zero current position, sent by subprocess and read by main process
            self.desired_pos = Queue()  # Servo zero desired position, sent by main and read by subprocess
            self.speed = Queue()  # Servo zero speed, sent by main and read by subprocess
            self.ServoBlaster = open('/dev/servoblaster', 'w')

    def move(self, position):
        self.ServoBlaster.write('0=' + str(position) + '\n')  #
        self.ServoBlaster.flush()