
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QLineEdit, QMessageBox, QFileDialog, QProgressBar
from PyQt5.QtWidgets import QListWidget, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
import datetime
import os
import sys
import PyQt5.QtWidgets as qt
import code.MatrixKeypad4x4 as keypad
import random as random
import pyautogui

from imutils.video import VideoStream
from imutils.video import FPS
from imutils import paths
import imutils
import face_recognition

import pickle
import cv2
import os
import json
import time

from gpiozero import Servo
from time import sleep
import RPi.GPIO as GPIO


relay_1_pin = 17

class MotorControlThread(QThread):

    is_run_motor = False
    GPIO.setwarnings(False)
    servo = Servo(18)
    GPIO.setup(relay_1_pin, GPIO.OUT, initial=GPIO.LOW)
    
    def turn_on_motor(self):
        global is_run_motor
        self.is_run_motor = True

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.servo.min()
    
    def run(self):
        while self._run_flag:
            if self.is_run_motor:
                self.is_run_motor = False
                print("motor on")
                GPIO.output(relay_1_pin, GPIO.HIGH)
                self.servo.max()
                sleep(10)
                GPIO.output(relay_1_pin, GPIO.LOW)
                self.servo.min()
        
    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


# from time import sleep
# import RPi.GPIO as GPIO




# class MotorControlThread(QThread):

#     is_run_motor = False
#     GPIO.setwarnings(False)
#     servo_pin = 17
#     GPIO.setmode(GPIO.BOARD)   # Use physical pin numbering
#     GPIO.setup(servo_pin, GPIO.OUT, initial=GPIO.LOW)
    
#     def turn_on_motor(self):
#         global is_run_motor
#         self.is_run_motor = True

#     def __init__(self):
#         super().__init__()
#         self._run_flag = True
    
#     def run(self):
#         while self._run_flag:
#             if self.is_run_motor:
#                 self.is_run_motor = False
#                 GPIO.output(servo_pin, GPIO.HIGH) # Turn on
#                 sleep(1)                  # Sleep for 1 second
#                 GPIO.output(servo_pin, GPIO.LOW)  # Turn off
        
#     def stop(self):
#         """Sets run flag to False and waits for thread to finish"""
#         self._run_flag = False
#         self.wait()


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    open_door_signal = pyqtSignal()

    is_take_snapshot = False
    is_recognize_user = True
    name_save_pic = "test.jpg"
    img_counter = 0
    data = []
    encodingsP = "encodings.pickle"
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    tolerance = 0.4
    text_show_screen = ""

    @pyqtSlot(bool)
    def restart_img_counter(self):
        global img_counter
        self.img_counter = 0

    # create global variable to control take snapshot
    @pyqtSlot(bool)
    def take_snapshot_enable(self):
        global is_take_snapshot
        self.is_take_snapshot = True

    def set_recognize_user(self, recognize_user):
        global is_recognize_user
        self.is_recognize_user = recognize_user

    def set_name(self, name):
        global name_save_pic
        self.name_save_pic = name
    
    def setText(self, name):
        global text_show_screen
        self.text_show_screen = name

    def set_tolerance(self, tolerance):
        self.tolerance = tolerance

    def del_all_user(self):
        global data
        self.data = pickle.loads(open(self.encodingsP, "rb").read())
        # delete all encodings
        self.data["encodings"] = []
        # delete all names
        self.data["names"] = []

        # save data
        f = open(self.encodingsP, "wb")
        f.write(pickle.dumps(self.data))
        f.close()
        # os delete dataset folder
        os.system("rm -rf dataset")
        self.reload_list()

    def __init__(self):
        super().__init__()
        self._run_flag = True
    

    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(0)
        self.data = pickle.loads(open(self.encodingsP, "rb").read())
        while self._run_flag:
            ret, cv_img = cap.read()
            _cv_img = cv_img
            cv_img = self.recognize_face(cv_img)
            # print(_listname)
            self.take_snapshot(_cv_img)
            if ret:
                self.change_pixmap_signal.emit(cv_img)

        cap.release()

    def take_snapshot(self, cv_img):
        global is_take_snapshot, name_save_pic, img_counter
        cv_img = cv2.resize(cv_img, (0, 0), fx=0.25, fy=0.25)
        if self.is_take_snapshot:
            print("take snapshot")
            self.create_dataset_folder("dataset")
            print("name_save", self.name_save_pic)
            self.create_dataset_folder("dataset/" + self.name_save_pic)
            # print("img_counter", img_counter)
            img_name = "dataset/" + self.name_save_pic + \
                "/image_{}.jpg".format(self.img_counter)
            cv2.imwrite(img_name, cv_img)
            print("{} written!".format(img_name))
            # global name_save, img_counter
            self.img_counter += 1
            self.is_take_snapshot = False
    
    def getIndexImg(self):
        return self.img_counter
    
    def reload_list(self):
        self.data = pickle.loads(open(self.encodingsP, "rb").read())

    def delete_user(self, name):
        # global data
        self.data = pickle.loads(open(self.encodingsP, "rb").read())
        # get names index of user
        index = self.data["names"].index(name)
        # delete encodings of user
        del self.data["encodings"][index]
        # delete names of user
        del self.data["names"][index]
        print("index", index)

        # save data
        f = open(self.encodingsP, "wb")
        f.write(pickle.dumps(self.data))
        f.close()

    def check_user_exist(self, name):

        data = pickle.loads(open(self.encodingsP, "rb").read())
        # parse data get names
        names = []
        for name_ in data["names"]:
            names.append(name_)
        print("names", names)
        if name in names:
            return True
        else:
            return False

    def get_user_list(self):

        data = pickle.loads(open(self.encodingsP, "rb").read())
        # parse data get names
        names = []
        for name in data["names"]:
            names.append(name)
        return names

    def recognize_face(self, frame):
        if self.is_recognize_user:
            # frame = cv2.resize(frame, (0, 0), fx=0.1, fy=0.1) #imutils.resize(frame, width=500)
            frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rects = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1,
                                                       minNeighbors=3, minSize=(30, 30),
                                                       flags=cv2.CASCADE_SCALE_IMAGE)
            boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]

            encodings = face_recognition.face_encodings(rgb, boxes)

            # # set text capture in frame
            # cv2.putText(frame, self.text_show_screen, (0, 20),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            y0, dy = 10, 15
            for i, line in enumerate(self.text_show_screen.split('\n')):
                y = y0 + i*dy
                cv2.putText(frame, line, (0, y ), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                
            try:
                names = []
                # data = pickle.loads(open(self.encodingsP, "rb").read())
                for encoding in encodings:
                    # set accuracy of recognition to 0.6
                    matches = face_recognition.compare_faces(
                        self.data["encodings"], encoding, tolerance=self.tolerance)
                    # matches = face_recognition.compare_faces(data["encodings"],
                    #                                         encoding)
                    name = "Unknown"
                    if True in matches:
                        matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                        counts = {}
                        for i in matchedIdxs:
                            name = self.data["names"][i]
                            counts[name] = counts.get(name, 0) + 1
                        name = max(counts, key=counts.get)
                        self.open_door_signal.emit()
                    names.append(name)

                for ((top, right, bottom, left), name) in zip(boxes, names):
                    cv2.rectangle(frame, (left, top),
                                (right, bottom), (0, 255, 0), 2)
                    y = top - 15 if top - 15 > 15 else top + 15
                    cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.75, (0, 255, 0), 2)
            except:
                print("error")

        return frame

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

    def create_dataset_folder(self, name):
        if not os.path.exists(name):
            os.makedirs(name)

class KeypadThread(QThread):
    keypad_input_signal = pyqtSignal(str)
    open_door_signal = pyqtSignal()

    key_input = ""
    data_lcd = ""

    option_add_new = 1
    option_delete_data = 2
    option_change_password = 3
    option_hide_menu = 4
    option_open_door = 5

    option_capture = 1
    option_training = 2
    option_back = 3

    option_password_title = 0
    option_delete_password = 1
    option_confirm_password = 2
    option_free_option = 10

    menu_main_options = {
        option_add_new: '1: Add new',
        option_delete_data: '2: Delete',
        option_change_password: '3: Change pass',
        option_hide_menu: '4: Hide',
        option_open_door: '5: Open Door'
    }

    menu_addnew_options = {
        option_capture: 'A: Capture',
        option_training: 'C: Training',
        option_back: 'B: Back',
    }

    menu_enter_password = {
        option_password_title: "",
        option_delete_password: 'D: Delete',
        option_confirm_password: 'C: Confirm',
        option_back: 'B: Back',
        option_free_option: "your pass: "
    }

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        is_show_menu = False
        while self._run_flag:
            try:
                key=keypad.readKey(keypad.col_list, keypad.row_list)
                if(key == keypad.show_menu_key):
                    self.print_menu(self.menu_main_options)
                    is_show_menu = True
                if(key == keypad.exit_program):
                    # self.keypad_input_signal.emit(key)
                    # os._exit(0)
                    pyautogui.click(100, 100)
                if is_show_menu:
                    option = ''
                    try:
                        option = int(key)
                    except:
                        print('Wrong input. Please enter a number ...')
                    #Check what choice was entered and act accordingly
                    if option == self.option_add_new:
                        time.sleep(1)
                        self.add_new_option()
                        self.print_menu(self.menu_main_options)
                    elif option == self.option_delete_data:
                        time.sleep(1)
                        self.delete_data_option()
                        self.print_menu(self.menu_main_options)
                    elif option == self.option_change_password:
                        time.sleep(1)
                        self.change_password_option()
                        self.print_menu(self.menu_main_options)
                    elif option == self.option_hide_menu:
                        print("hide/show")
                        self.hide_menu_option()
                        is_show_menu = False
                    elif option == self.option_open_door:
                        time.sleep(1)
                        print("option_open_door")
                        self.open_door()
                        self.print_menu(self.menu_main_options)
                    else:
                        print('Invalid option. Please enter a number between 1 and 4.')
            except KeyboardInterrupt:
                GPIO.cleanup()
                sys.exit()
    def add_new_option(self):
        print("add_new_option")
        admin_pass = self.get_password_from_file()
        input_pass = self.get_password_authentication("add new")
        if input_pass == None:
            return
        if(input_pass == admin_pass):
            data_menu = self.menu_addnew_options
            self.send_text_main_screen("successfully")
            time.sleep(2)
            self.print_menu(data_menu)
            while True:
                try:
                    key=keypad.readKey(keypad.col_list, keypad.row_list)
                    if key != None:
                        if key is keypad.capture_key:
                            print("capture")
                            self.send_text_main_screen(keypad.capture_key)
                        if key is keypad.training_key:
                            self.send_text_main_screen(keypad.training_key)
                            print("training")
                            return
                        time.sleep(0.3) # gives user enoght time to release without having double inputs
                except KeyboardInterrupt:
                    GPIO.cleanup()
                    sys.exit()
        else:
            self.send_text_main_screen("password false")
            time.sleep(2)

    def get_password_authentication(self, title):
        data_menu = self.menu_enter_password
        data_menu[self.option_password_title] = title
        self.print_menu(data_menu)
        password = ""
        while True:
            try:
                key=keypad.readKey(keypad.col_list, keypad.row_list)
                if key != None:
                    
                    if key not in keypad.function_keys:
                        password = password + key
                        data_menu[self.option_free_option] = "your password:\n" + password
                        self.print_menu(data_menu)
                    if key is keypad.delete_key:
                        len_key = len(password)
                        if len_key > 0:
                            password  = password[:len_key-1]
                        data_menu[self.option_free_option] = "your password:\n" + password
                        self.print_menu(data_menu)
                    if key is keypad.back_key:
                        return None
                    if key is keypad.confirm_key:
                        return password
                    time.sleep(0.3) # gives user enoght time to release without having double inputs
            except KeyboardInterrupt:
                GPIO.cleanup()
                sys.exit()

    def delete_data_option(self):
        print("delete_data_option")
        admin_pass = self.get_password_from_file()
        input_pass = self.get_password_authentication("delete")
        if input_pass == None:
            return
        if(input_pass == admin_pass):
            time.sleep(2)
            self.send_text_main_screen(keypad.delete_key)
            time.sleep(2)
            self.send_text_main_screen("delete done")
            time.sleep(2)
        else:
            self.send_text_main_screen("password false")
            time.sleep(2)

    def open_door(self):
        admin_pass = self.get_password_from_file()
        input_pass = self.get_password_authentication("open door")
        if input_pass == None:
            return
        if(input_pass == admin_pass):
            self.open_door_signal.emit()
            time.sleep(2)
            self.send_text_main_screen("door is open")
            time.sleep(2)
        else:
            self.send_text_main_screen("password false")
            time.sleep(2)

    def change_password_option(self):
        print("change_password_option")
        admin_pass = self.get_password_from_file()
        input_pass = self.get_password_authentication("old pass")
        if input_pass == None:
            return
        if(input_pass == admin_pass):
            time.sleep(2)
            newpass = self.get_password_authentication("new pass")
            if newpass == None:
                self.send_text_main_screen("cancel")
                time.sleep(2)
                return
            if len(newpass) < 4:
                self.send_text_main_screen("password \ntoo short")
                time.sleep(2)
                return
            self.save_password_to_file(newpass)
            self.send_text_main_screen("change password \nsuccessfully")
            time.sleep(2)
            

    def hide_menu_option(self):
        self.keypad_input_signal.emit("")
        print("hide_menu_option")

    def print_menu(self, menu):
        global data_lcd
        self.data_lcd = ""
        for key in menu.keys():
            self.data_lcd = self.data_lcd + menu[key] + "\n"
        self.keypad_input_signal.emit(self.data_lcd)
        
    def get_password_from_file(self):
        with open('password.txt', 'r') as f:
            return f.read()
    
    def save_password_to_file(self, password):
        with open('password.txt', 'w') as f:
            f.write(password)
        
    def send_text_main_screen(self, text):
        self.keypad_input_signal.emit(text)
    
    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

class App(QWidget):
    thread = VideoThread()
    name_save = "test"
    # is_capture_new = True
    showRecognize = True

    password_input = ""

    create_new_name = True

    keypadThread = KeypadThread()

    motorThread = MotorControlThread()

    def __init__(self):
        super().__init__()
        # self.init_variables()
        self.setWindowState(Qt.WindowFullScreen)
        self.setWindowTitle("Face Rec")
        self.disply_width = 300
        self.display_height = 300
        self.image_label = QLabel(self)
        self.image_label.resize(300, 300)
        self.image_label.setScaledContents(True)
        self.image_label.move(0, 0)
        self.textLabel = QLabel('Webcam')
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.open_door_signal.connect(self.opendoor)
        self.thread.start()

        self.keypadThread.keypad_input_signal.connect(self.keypad_update)
        self.keypadThread.open_door_signal.connect(self.opendoor)
        self.keypadThread.start()


        self.motorThread.start()



    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    def del_all_user(self):
        self.thread.del_all_user()

    def take_snapshot(self):
        print("take_snapshot")
        self.thread.take_snapshot_enable()

    def training_data(self):
        print("[INFO] start processing faces...")
        imagePaths = list(paths.list_images("dataset"))
        # filter image paths if they are not images
        # just get image path contain name_save
        imagePaths = [p for p in imagePaths if self.name_save in p]
        print("imagePaths", imagePaths)
        encodingsP = "encodings.pickle"
        data = pickle.loads(open(encodingsP, "rb").read())
        # initialize the list of known encodings and known names
        knownEncodings = data["encodings"]
        knownNames = data["names"]
        # loop over the image paths
        for (i, imagePath) in enumerate(imagePaths):
            print("imagePath", imagePath, "i", i)
            # extract the person name from the image path
            print("[INFO] processing image {}/{}".format(i + 1,
                                                         len(imagePaths)))
            name = imagePath.split(os.path.sep)[-2]
            image = cv2.imread(imagePath)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb,
                                                    model="hog")
            encodings = face_recognition.face_encodings(rgb, boxes)
            for encoding in encodings:
                # check name not exist in knownNames
                print("name", name)
                if name not in knownNames:
                    # add name to knownNames
                    knownNames.append(name)
                    # add encoding to knownEncodings
                    knownEncodings.append(encoding)
        # dump the facial encodings + names to disk
        print("[INFO] serializing encodings...")
        data = {"encodings": knownEncodings, "names": knownNames}
        f = open("encodings.pickle", "wb")
        f.write(pickle.dumps(data))
        f.close()
        # update user list
        list_users = self.thread.get_user_list()

    def tolerance_option_button_change_value(self, value):
        print("option_button_change_value", self.option_button.currentText())
        self.thread.set_tolerance(float(self.option_button.currentText()))

    # def show_alert(timeout, text):


    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)
    
    @pyqtSlot()
    def opendoor(self):
        self.motorThread.turn_on_motor()

    @pyqtSlot(str)
    def keypad_update(self, key):
        if key == keypad.capture_key:
            if self.create_new_name:
                self.create_new_name = False
                self.name_save = str(random.randrange(1000, 10000))
            self.thread.set_name(self.name_save)
            self.take_snapshot()
            self.thread.setText("capture: " + str(self.thread.getIndexImg() + 1) + "\nname: " + self.name_save)
        elif key == keypad.training_key:
            self.training_data()
            self.create_new_name = True
            self.thread.setText("training data \n done")
            self.thread.reload_list()
        elif key == keypad.delete_key:
            self.thread.setText("delete all data")
            self.thread.del_all_user()
        else:
            self.thread.setText(key)
        # global showRecognize, name_save, create_new_name
        # print("key: ", key)
        # if(key == keypad.add_new_key):
        #     print("add_new_key")
        #     self.thread.setText("#: enter, D: del\nenter password: ")
        # elif(key == keypad.enter_key):
        #     print("enter_key")
        #     os._exit(0)
        # elif(key == keypad.capture_key):
        #     print("capture_key face")
        #     if self.create_new_name:
        #         self.create_new_name = False
        #         self.name_save = str(random.randrange(1000, 10000))
        #     self.thread.setText("capture: " + str(self.thread.getIndexImg() + 1) + "\nname: " + self.name_save)
        #     self.thread.set_name(self.name_save)
        #     self.take_snapshot()
        # elif(key == keypad.recognition_enable_key):
        #     print("recognition_enable_key")
        #     self.showRecognize = not self.showRecognize
        #     if self.showRecognize:
        #         self.thread.setText("recognize")
        #     else:
        #         self.thread.setText("camera")
        #     self.thread.set_recognize_user(self.showRecognize)
        # elif(key == keypad.training_key):
        #     print("training_key face")
        #     self.thread.setText("training data")
        #     self.thread.restart_img_counter()
        #     self.training_data()
        #     self.thread.setText("training data \n done")
        #     self.create_new_name = True
        # elif(key == keypad.delete_key):
        #     print("delete_key face")
        #     self.thread.setText("delete all data")
        #     self.thread.del_all_user()
            
        # else:
        #     password_input = key
        #     self.thread.setText("password: \n" + password_input)


    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(
            rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(
            self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())
