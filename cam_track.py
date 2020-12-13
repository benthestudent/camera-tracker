from multiprocessing import Process, Queue
import time
import cv2
from Servo import Servo

# define x- and y-axis servos with upper lims and lower lims
xServo = Servo(upper_limit=230, lower_limit=70, blaster_str="0=")
yServo = Servo(upper_limit=250, lower_limit=75, blaster_str="1=")

webcam = cv2.VideoCapture(0)  # Get ready to start getting images from the webcam
webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # I have found this to be about the highest-
webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # resolution you'll want to attempt on the pi

frontalface = cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml")  # frontal face pattern detection
profileface = cv2.CascadeClassifier("haarcascade_profileface.xml")  # side face pattern detection

max_face_recog_attempt = 3
face = [0, 0, 0, 0]  # This will hold the array that OpenCV returns when it finds a face: (makes a rectangle)
Cface = [0, 0]  # Center of the face: a point calculated from the above variable
lastface = 0  # int 1-3 used to speed up detection. The script is looking for a right profile face,-


# 	a left profile face, or a frontal face; rather than searching for all three every time,-
# 	it uses this variable to remember which is last saw: and looks for that again. If it-
# 	doesn't find it, it's set back to zero and on the next loop it will search for all three.-
# 	This basically tripples the detect time so long as the face hasn't moved much.

def servo_controller(servo):  # Process 0 controlles servo0
    speed = .1  # Here we set some defaults:
    temp_current = 99  # by making the current position and desired position unequal,-
    temp_desired = 100  # we can be sure we know where the servo really is. (or will be soon)
    while True:
        time.sleep(speed)
        if servo.current_pos.empty():  # Constantly update Servo0CP in case the main process needs-
            servo.current_pos.put(temp_current)  # to read it
        if not servo.desired_pos.empty():  # Constantly read read Servo0DP in case the main process-
            temp_desired = servo.desired_pos.get()  # has updated it
        if not servo.speed.empty():  # Constantly read read Servo0S in case the main process-
            temp_speed = servo.speed.get()  # has updated it, the higher the speed value, the shorter-
            speed = .1 / temp_speed  # the wait between loops will be, so the servo moves faster
        if not temp_current != temp_desired:
            temp_current = temp_current + 1 if temp_current < temp_desired else temp_current - 1
            servo.current_pos.put(temp_current)  # move the servo that little bit
            servo.move(temp_current)
            if not servo.current_pos.empty():  # throw away the old Servo0CP value,-
                trash = servo.current_pos.get()  # it's no longer relevent
        else:  # if all is good,-
            temp_speed = 1  # slow the speed; no need to eat CPU just waiting


Process(target=servo_controller, args=(xServo,)).start()  # Start the subprocesses
Process(target=servo_controller, args=(yServo,)).start()  #
time.sleep(1)  # Wait for them to start


def cam_move(distance, speed, direction):  # To move right, we are provided a distance to move and a speed to move.
    servo = xServo if direction in ["left", "right"] else yServo
    if not servo.current_pos.empty():  # Read it's current position given by the subprocess(if it's avalible)-
        temp_current = servo.current_pos.get()  # and set the main process global variable.
    temp_desired = temp_current + distance if direction in ["right",
                                                            "down"] else temp_current - distance  # The desired position is the current position + the distance to move.
    if temp_desired > servo.upper_limit:  # But if you are told to move further than the servo is built go...
        temp_desired = servo.upper_limit  # Only move AS far as the servo is built to go.
    if temp_desired < servo.lower_limit:
        temp_desired = servo.lower_limit
    servo.desired_pos.put(temp_desired)  # Send the new desired position to the subprocess
    servo.speed.put(speed)  # Send the new speed to the subprocess
    return True


while True:

    faceFound = False  # This variable is set to true if, on THIS loop a face has already been found
    # We search for a face three diffrent ways, and if we have found one already-
    # there is no reason to keep looking.

    attempt = 0
    face = frontalface
    while attempt < max_face_recog_attempt:
        face = frontalface if lastface == 0 or lastface == 1 else profileface
        aframe = webcam.read()[1]  # there seems to be an issue in OpenCV or V4L or my webcam-
        aframe = webcam.read()[1]  # driver, I'm not sure which, but if you wait too long,
        aframe = webcam.read()[1]  # the webcam consistantly gets exactly five frames behind-
        aframe = webcam.read()[1]  # realtime. So we just grab a frame five times to ensure-
        aframe = webcam.read()[1]  # we have the most up-to-date image.
        fface = face.detectMultiScale(aframe, 1.3, 4, (
                cv2.CASCADE_DO_CANNY_PRUNING + cv2.CASCADE_FIND_BIGGEST_OBJECT + cv2.CASCADE_DO_ROUGH_SEARCH),
                                      (60, 60))
        if fface != ():  # if we found a frontal face...
            lastface = attempt + 1  # set lastface 1 (so next loop we will only look for a frontface)
            for f in fface:  # f in fface is an array with a rectangle representing a face
                faceFound = True
                face = f
                break
        else:
            attempt += 1
            face = profileface

    if not faceFound:  # if no face was found...-
        lastface = 0  # the next loop needs to know
        face = [0, 0, 0, 0]  # so that it doesn't think the face is still where it was last loop

    x, y, w, h = face
    Cface = [(w / 2 + x), (h / 2 + y)]  # we are given an x,y corner point and a width and height, we need the center
    print(str(Cface[0]) + "," + str(Cface[1]))

    if Cface[0] != 0:  # if the Center of the face is not zero (meaning no face was found)
        if Cface[0] > 180:  # The camera is moved diffrent distances and speeds depending on how far away-
            cam_move(5, 1, "left")  # from the center of that axis it detects a face
        if Cface[0] > 190:  #
            cam_move(7, 2, "left")  #
        if Cface[0] > 200:  #
            cam_move(9, 3, "left")  #

        if Cface[0] < 140:  # and diffrent dirrections depending on what side of center if finds a face.
            cam_move(5, 1, "right")
        if Cface[0] < 130:
            cam_move(7, 2, "right")
        if Cface[0] < 120:
            cam_move(9, 3, "right")

        if Cface[1] > 140:  # and moves diffrent servos depending on what axis we are talking about.
            cam_move(5, 1, "down")
        if Cface[1] > 150:
            cam_move(7, 2, "down")
        if Cface[1] > 160:
            cam_move(9, 3, "down")

        if Cface[1] < 100:
            cam_move(5, 1, "up")
        if Cface[1] < 90:
            cam_move(7, 2, "up")
        if Cface[1] < 80:
            cam_move(9, 3, "up")
