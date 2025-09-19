# -*- coding: utf-8 -*-
import socket
import sys
import math
from naoqi import ALProxy

import serial
import time

# ======================= Pepper Setup ==========================
choreo = "localhost:50867" # change 
ROBOT_IP, port_str = choreo.split(":")
ROBOT_PORT = int(port_str)       
SERVER_IP = "0.0.0.0"
SERVER_PORT = 12345

awareness = ALProxy("ALBasicAwareness", ROBOT_IP, ROBOT_PORT)
awareness.pauseAwareness()
awareness.stopAwareness()

life_proxy = ALProxy("ALAutonomousLife", ROBOT_IP, ROBOT_PORT)
tts = ALProxy("ALTextToSpeech", ROBOT_IP, ROBOT_PORT)
tts.say("my name is pepper")
life_proxy.setState("safeguard")
print("Life state:", life_proxy.getState())

motion = ALProxy("ALMotion", ROBOT_IP, ROBOT_PORT)

def set_stiffness(motion, body_part, stiffness):
    motion.setStiffnesses(body_part, stiffness)

def grasp_hand(motion, hand_name):
    set_stiffness(motion, hand_name, 1.0)
    motion.setAngles(hand_name, 0.0, 1.0)

def release_hand(motion, hand_name):
    set_stiffness(motion, hand_name, 1.0)
    motion.setAngles(hand_name, 1.0, 1.0)

def set_initial_positions(motion):
    motion.setAngles("HeadYaw", math.radians(0), True)
    motion.setAngles("HeadPitch", math.radians(0), True)
    motion.setAngles("LShoulderPitch", math.radians(0), True)
    motion.setAngles("LShoulderRoll", math.radians(25), True)
    motion.setAngles("LElbowRoll", math.radians(-85), True)
    motion.setAngles("LElbowYaw", math.radians(-16), True)
    motion.setAngles("RShoulderPitch", math.radians(0), True)
    motion.setAngles("RShoulderRoll", math.radians(-25), True)
    motion.setAngles("RElbowRoll", math.radians(85), True)
    motion.setAngles("RElbowYaw", math.radians(16), True)
    motion.setAngles("RWristYaw", math.radians(6), True)
    motion.setAngles("LWristYaw", math.radians(6), True)
    release_hand(motion, "LHand")
    release_hand(motion, "RHand")

set_initial_positions(motion)

# ================== Mapping constants ==========================
MAPPING_CONSTANTS = {
    "HR": {"input": (-100, -180), "output": (-90, 0)},
    "HL": {"input": (100, 180), "output": (90, 0)},
    "HU": {"input": (-40, 40), "output": (25, -40)},
    "3": {"input": (-90, -180), "output": (-90, 0)},
    "4": {"input": (-70, 0), "output": (5, -85)},
    "5": {"input": (-80, -30), "output": (10, 80)},
    "6": {"input": (-90, 90), "output": (-90, 90)},
    "7": {"input": (-70, 0), "output": (5, 85)},
    "8": {"input": (-80, -30), "output": (-10, -80)},
    "9": {"input": (-90, 90), "output": (90, -90)},
    "10": {"input": (-90, -180), "output": (-90, 0)},
    "11": {"input": (180, 90), "output": (0, 90)},
    "12": {"input": (180, 90), "output": (0, 90)}
}

# ================== Unity Packet Handling =======================
last_valid_data = None
EXPECTED_VALUES = 49 + 7  # 7 trackers * (3+4) + 7 extras

def parse_data(data_str):
    try:
        data_str = data_str.strip()
        if not data_str:
            return None
        if data_str.endswith(","):
            data_str = data_str[:-1]
        parts = data_str.replace("(", "").replace(")", "").split(",")
        values = [float(x) for x in parts if x.strip() != ""]
        if len(values) != EXPECTED_VALUES:
            print("[W] Incomplete packet received. Got {} values, expected {}.".format(len(values), EXPECTED_VALUES))
            return None
        return values
    except Exception as e:
        print("[E] Parse error:", e, "Raw data:", data_str)
        return None

# ================== Server ======================================
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(1)
    print("Listening for connections on {}:{}".format(SERVER_IP, SERVER_PORT))
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print("Accepted connection from {}".format(client_address))
            try:
                handle_client(client_socket)
            except Exception as e:
                print("Error handling client: {}".format(e))
            finally:
                client_socket.close()
    except KeyboardInterrupt:
        print("Server shutting down.")
    finally:
        server_socket.close()

def handle_client(client_socket):
    global last_valid_data
    buffer = ""
    while True:
        data = client_socket.recv(4096)
        if not data:
            break
        buffer += data.decode("utf-8")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            values = parse_data(line)
            if values:
                last_valid_data = values
                print_received_data(values)
            else:
                if last_valid_data:
                    print("[!] Using last valid dataset")
                    print_received_data(last_valid_data)

# ================== Processing ==================================
def print_received_data(values):
    # <=== your full existing quaternion/euler → mapping → motion code goes here ===>
    # I’m not altering your math/motion section, only replacing “received_data parsing” 
    # with our safe parsed `values` list.
    # lines = received_data.strip().split('\n')
    # for line in lines:
    # values = line.strip().split(',')
    
    head_rot = extract_numbers(values[3:7])
    head_euler = quaternion_to_euler(head_rot)

    right_shoulder_rot = extract_numbers(values[10:14])  
    Rshoulder_euler = quaternion_to_euler(right_shoulder_rot)
        
    left_shoulder_rot = extract_numbers(values[17:21])  
    Lshoulder_euler = quaternion_to_euler(left_shoulder_rot)
        
    right_forearm_rot = extract_numbers(values[24:28])
    Rforearm_euler = quaternion_to_euler(right_forearm_rot)
        
    left_forearm_rot = extract_numbers(values[31:35])
    Lforearm_euler = quaternion_to_euler(left_forearm_rot)

    right_hand_rot = extract_numbers(values[38:42]) #
    Rhand_euler = quaternion_to_euler(right_hand_rot)
        
    left_hand_rot = extract_numbers(values[45:49]) #
    Lhand_euler = quaternion_to_euler(left_hand_rot)

    buttons = extract_numbers(values[49:55])
    debugP = int(buttons[0]) 
    # print("debug:{}".format(buttons[0]),"gripL:{}".format(buttons[1]),"gripR:{}".format(buttons[2]),"GearR:{}".format(buttons[3]),"GearL:{}".format(buttons[4]),"GearLS:{}".format(buttons[5]))
    gripL = int(buttons[1]) 
    gripR = int(buttons[2]) 

    GearR = int(buttons[3])
    GearL = int(buttons[4])
    GearLS = int(buttons[5])
    # print("debug:{}".format(buttons[0]),"gripL:{}".format(buttons[1]),"gripR:{}".format(buttons[2]),"GearR:{}".format(buttons[3]),"GearL:{}".format(buttons[4]),"GearLS:{}".format(buttons[5]))
    print(gripL,gripR,GearR,GearL,GearLS)

#################################################################################### EDIT
    x_head_angle = round(math.degrees(head_euler[0]))
    y_head_angle = round(math.degrees(head_euler[1]))
    z_head_angle = round(math.degrees(head_euler[2]))
###
    x_RS_angle = round(math.degrees(Rshoulder_euler[0])) # altered
    y_RS_angle = round(math.degrees(Rshoulder_euler[1]))
    z_RS_angle = round(math.degrees(Rshoulder_euler[2]))
        
    # if z_RS_angle > -70:
    #     x_RS_angle = abs(abs(x_RS_angle) - 180)
    # else:
    #     x_RS_angle = abs(x_RS_angle) - 180

    x_LS_angle = round(math.degrees(Lshoulder_euler[0])) # altered
    y_LS_angle = round(math.degrees(Lshoulder_euler[1]))
    z_LS_angle = round(math.degrees(Lshoulder_euler[2]))
    if z_LS_angle > 0:
        z_LS_angle = -z_LS_angle
    else : 
        z_LS_angle = z_LS_angle

    if z_LS_angle > 0:
        z_RS_angle = z_RS_angle
    else : 
        z_RS_angle = -z_RS_angle

    if z_LS_angle < -130:
        x_LS_angle = max(x_LS_angle, -15)
    # if abs(z_RS_angle) > 115:
    #     x_RS_angle = max(x_RS_angle, -15)
    if abs(z_RS_angle) < 0:
        x_RS_angle = max(x_RS_angle, -15)
    x_RF_angle = round(math.degrees(Rforearm_euler[0]))
    y_RF_angle = round(math.degrees(Rforearm_euler[1]))
    z_RF_angle = round(math.degrees(Rforearm_euler[2]))

    x_LF_angle = round(math.degrees(Lforearm_euler[0]))
    y_LF_angle = round(math.degrees(Lforearm_euler[1]))
    z_LF_angle = round(math.degrees(Lforearm_euler[2]))
###
    x_RH_angle = round(math.degrees(Rhand_euler[0])) #
    y_RH_angle = round(math.degrees(Rhand_euler[1])) #
    z_RH_angle = round(math.degrees(Rhand_euler[2])) #

    x_LH_angle = round(math.degrees(Lhand_euler[0])) # 
    y_LH_angle = round(math.degrees(Lhand_euler[1])) #
    z_LH_angle = round(math.degrees(Lhand_euler[2])) #

    # processing of data before being sent to the robot 
    mapped_1 = max(-40, min(25, round(map_value(y_head_angle, "HU"))))
    if z_head_angle < 0:
        mapped_2 = float("{:.0f}".format(map_value(z_head_angle,"HR")))
    else:
        mapped_2 = float("{:.0f}".format(map_value(z_head_angle,"HL")))
    mapped_2 = max(-119.0, min(119.0, mapped_2))
###     # Right arm
    if x_RS_angle < 0:
        mapped_3 = float("{:.0f}".format(map_value(x_RS_angle, "3")))
    else:
        mapped_3 = float("{:.0f}".format(map_value(x_RS_angle, "12")))
    mapped_3 = max(-75.0, min(75.0, mapped_3))
    mapped_4 = max(-50.0, min(-0.0, round(map_value(y_RS_angle, "4"))))
    mapped_5 = max(0.0, min(89.0, round(map_value(y_RF_angle, "5"))))
    # Left arm
    mapped_6 = max(-75.0, min(75.0, round(map_value(x_LS_angle, "6"))))
    mapped_7 = max(0.0, min(50.0, round(map_value(y_LS_angle, "7"))))
    mapped_8 = max(-89.0, min(-0.0, round(map_value(y_LF_angle, "8"))))
###     # hands 
    mapped_9 = max(-104.0, min(104.0, round(map_value(x_RH_angle, "9")))) #
    if x_LH_angle < 0:
        mapped_10 = float("{:.0f}".format(map_value(x_LH_angle, "10")))
    else:
        mapped_10 = float("{:.0f}".format(map_value(x_LH_angle, "11")))
    mapped_10 = max(-104.0, min(104.0, mapped_10))

    print ("*********************************")
    print ("debug:{}".format(debugP),"gripL:{}".format(gripL),"gripR:{}".format(gripR))
    print ("1- Mapped HU from y_head i1 : {}".format(mapped_1))
    print ("2- Mapped HRL from z_head i2 : {}".format(mapped_2))
    print ("3- Mapped RShoulderPitch from x_RS i3 : {}".format(mapped_3))
    print ("4- Mapped RShoulderRoll from y_RS i4 : {}".format(mapped_4))
    print ("5- Mapped RElbowRoll from y_RF i7 : {}".format(mapped_5))       ####      
    print ("6- Mapped LShoulderPitch from x_LS i9 : {}".format(mapped_6))
    print ("7- Mapped LShoulderRoll from y_LS i10 : {}".format(mapped_7))
    print ("8- Mapped LElbowRoll from y_LF i13 : {}".format(mapped_8))      ####
    print ("9- Mapped RWristYaw from x_RH i15 : {}".format(mapped_9)) #
    print ("10- Mapped LWristYaw from x_LH i18 : {}".format(mapped_10)) # 
    
    if gripL == 0 :
        release_hand(motion, "LHand")
    else :
        grasp_hand(motion, "LHand")

    if gripR == 0 :
        release_hand(motion, "RHand")
    else :
        grasp_hand(motion, "RHand")

    # Gear values 
    x, y, theta = 0.0 , 0.0 , 0.0
    # forward backward gear R
    if GearR == 1:
        x = 0.2
    elif GearR == -1:
        x = -0.2

    # rotaion gear L
    if GearL == 1:
        theta = -0.1
    elif GearL == -1:
        theta = 0.1

    motion.move(x, y, theta)



    # Send GearLS to the serial port

    GearLS = int(buttons[5])  # Assuming GearLS is the 6th button

    servo = 0

# servo
    # if GearLS == -1:
    #     servo = -1
    #     ser.write(str(servo) + "\n")  # Convert 'servo' to a string before sending


    # elif GearLS == 1:
    #     servo = 1
    #     ser.write(str(servo) + "\n")  # Convert 'servo' to a string before sending
# servo



    # servo = GearLS
    # ser.write("{}\n".format(servo).encode())  # Compatible with Python 2.7
    # time.sleep(1)  # Delay before sending again (adjust as needed)

#################################################################################### EDIT
    # Call debugPrint with the required parameters
    if debugP == 1 :
        debugPrint(head_rot, x_head_angle, y_head_angle, z_head_angle,
               right_shoulder_rot, x_RS_angle, y_RS_angle, z_RS_angle,
               left_shoulder_rot, x_LS_angle, y_LS_angle, z_LS_angle,
               right_forearm_rot, x_RF_angle, y_RF_angle, z_RF_angle,
               left_forearm_rot, x_LF_angle, y_LF_angle, z_LF_angle,
               right_hand_rot, x_RH_angle, y_RH_angle, z_RH_angle, # 
               left_hand_rot, x_LH_angle, y_LH_angle, z_LH_angle # 
               )
########################################################################################### Choreo
    # Check if head_euler contains at least three elements
    if len(head_euler) >= 3:  # WHY  
        # head 
        # motion.setAngles("HeadPitch", math.radians(mapped_1), True)
        # motion.setAngles("HeadYaw", math.radians(mapped_2), True)
        # right arm 
        motion.setAngles("RShoulderPitch", math.radians(mapped_3), True)
        motion.setAngles("RShoulderRoll", math.radians(mapped_4), True)
        motion.setAngles("RElbowRoll", math.radians(mapped_5), True)        ####
        # left arm 
        motion.setAngles("LShoulderPitch", math.radians(mapped_6), True)
        motion.setAngles("LShoulderRoll", math.radians(mapped_7), True)
        motion.setAngles("LElbowRoll", math.radians(mapped_8), True)        ####
        # hands 
        motion.setAngles("RWristYaw", math.radians(mapped_9), True) #
        motion.setAngles("LWristYaw", math.radians(mapped_10), True) #
    else:
        print("Error: Not enough Euler angles.")
########################################################################################### Choreo

# Functions #
def map_value(input_value, key):
    input_min, input_max = MAPPING_CONSTANTS[key]["input"]
    output_min, output_max = MAPPING_CONSTANTS[key]["output"]
    return output_min + (input_value - input_min) * (output_max - output_min) / (input_max - input_min)

# def extract_numbers(value_list):
#     return [float(value.replace('(', '').replace(')', '').strip()) for value in value_list]
def extract_numbers(value_list):
    return [float(value) for value in value_list]

def quaternion_to_euler(q):
    w, x, y, z = q
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x**2 + y**2))  
    sin_pitch = 2 * (w * y - z * x)
    if abs(sin_pitch) >= 1:
        pitch = math.copysign(math.pi / 2, sin_pitch)  
    else:
        pitch = math.asin(sin_pitch)
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y**2 + z**2))
    return roll, pitch, yaw

def debugPrint(head_rot, x_head_angle, y_head_angle, z_head_angle,
               right_shoulder_rot, x_RS_angle, y_RS_angle, z_RS_angle,
               left_shoulder_rot, x_LS_angle, y_LS_angle, z_LS_angle,
               right_forearm_rot, x_RF_angle, y_RF_angle, z_RF_angle,
               left_forearm_rot, x_LF_angle, y_LF_angle, z_LF_angle,
               right_hand_rot, x_RH_angle, y_RH_angle, z_RH_angle, # 
               left_hand_rot, x_LH_angle, y_LH_angle, z_LH_angle): # 
    print("Printing ... ")               
    # print("Head Rotation:", head_rot)
    # print("X Euler Head Angle:", x_head_angle)
    # print("Y Euler Head Angle:", y_head_angle)
    # print("Z Euler Head Angle:", z_head_angle)
             
    print("Right Shoulder Rotation:", right_shoulder_rot)
    print("X RS Euler Angle:# 3", x_RS_angle) # 3
    print("Y RS Euler Angle:# 4", y_RS_angle) # 4
    print("Z RS Euler Angle:", z_RS_angle)
                          
    # print("Right Forearm Rotation:", right_forearm_rot)          ####
    # print("X RF Euler Angle:", x_RF_angle)
    # print("Y RF Euler Angle:# 5", y_RF_angle) # 7
    # print("Z RF Euler Angle:", z_RF_angle)

    print("Left Shoulder Rotation:", left_shoulder_rot)
    print("X LS Euler Angle:# 6", x_LS_angle) # 9
    print("Y LS Euler Angle:# 7", y_LS_angle) # 10
    print("Z LS Euler Angle:", z_LS_angle)
            
    # print("Left Forearm Rotation:", left_forearm_rot)          ####
    # print("X LF Euler Angle:", x_LF_angle)
    # print("Y LF Euler Angle:# 8", y_LF_angle) # 13 
    # print("Z LF Euler Angle:", z_LF_angle)   

    # print("Right Hand Rotation:", right_hand_rot)
    # print("X RH Euler Angle:# 9", x_RH_angle)# x
    # print("Y RH Euler Angle:", y_RH_angle) 
    # print("Z RH Euler Angle:", z_RH_angle)

    # print("Left Hand Rotation:", left_hand_rot)
    # print("X LH Euler Angle:# 10", x_LH_angle)# y 
    # print("Y LH Euler Angle:", y_LH_angle) 
    # print("Z LH Euler Angle:", z_LH_angle)

if __name__ == "__main__":
    start_server()
    # ser.close()
