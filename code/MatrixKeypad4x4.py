

import RPi.GPIO as GPIO
import sys
import time

# define PINs according to cabling
# following array matches 1,2,3,4 PINs from 4x4 Keypad Matrix
# col_list=[21,20,16,26]
# row_list=[19,13,6,12]
# following array matches 5,6,7,8 PINs from 4x4 Keypad Matrix
row_list=[26,16,20,21]
col_list=[12,6,13,19]

delete_key = "D"
add_new_key = "A"
enter_key = "#"
capture_key = "A"
confirm_key = "C"
training_key = "C"
recognition_enable_key = "*"
show_menu_key = "A"
exit_program = "D"
back_key = "B"

function_keys = ["A", "B", "C", "D", "*", "#"]

# set row pins to output, all to high
GPIO.setmode(GPIO.BCM)
for pin in row_list:
  GPIO.setup(pin,GPIO.OUT)
  GPIO.output(pin, GPIO.HIGH)

#set columns pins to input. We'll read user input here
for pin in col_list:
  GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

key_map=[["D","#","0","*"],\
        ["C","9","8","7"],\
        ["B","6","5","4"],\
        ["A","3","2","1"]]

# define Matrix Keypad read function
def readKey(cols,rows):
  for r in rows:
    GPIO.output(r, GPIO.LOW)
    result=[GPIO.input(cols[0]),GPIO.input(cols[1]),GPIO.input(cols[2]),GPIO.input(cols[3])]
    if min(result)==0:
      key=key_map[int(rows.index(r))][int(result.index(0))]
      GPIO.output(r, GPIO.HIGH) # manages key keept pressed
      return(key)
    GPIO.output(r, GPIO.HIGH)

# main program
# while True:
#   try:
#     key=Keypad4x4Read(col_list, row_list)
#     if key != None:
#       print("You pressed: "+key)
#       time.sleep(0.3) # gives user enoght time to release without having double inputs
# # PINs final cleaning on interrupt
#   except KeyboardInterrupt:
#     GPIO.cleanup()
#     sys.exit()
