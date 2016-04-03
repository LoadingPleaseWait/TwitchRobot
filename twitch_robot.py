#!/usr/bin/env python3

import re
import socket
import RPi.GPIO as GPIO
import time
import sys

# chat code based on https://www.sevadus.tv/forums/index.php?/topic/774-simple-python-irc-bot/

HOST = "irc.chat.twitch.tv"                          # Hostname of the IRC-Server in this case twitch's
PORT = 6667                                     # Default IRC-Port
CHAN = "#mocitytexhardhead"                               # Channelname = #{Nickname}
NICK = "loadingpw"                                # Nickname = Twitch username
PASS = "insertoauthtokenhere"   # www.twitchapps.com/tmi/ will help to retrieve the required authkey

RIGHT_MOTOR = 7
LEFT_MOTOR = 12


def send_pong(msg):
    con.send(bytes('PONG %s\r\n' % msg, 'UTF-8'))

# send a message on the twitch chat
def send_message(chan, msg):
    con.send(bytes('PRIVMSG %s :%s\r\n' % (chan, msg), 'UTF-8'))

# send username
def send_nick(nick):
    con.send(bytes('NICK %s\r\n' % nick, 'UTF-8'))

# authenticate
def send_pass(password):
    con.send(bytes('PASS %s\r\n' % password, 'UTF-8'))

# join a twitch chat
def join_channel(chan):
    con.send(bytes('JOIN %s\r\n' % chan, 'UTF-8'))

def part_channel(chan):
    con.send(bytes('PART %s\r\n' % chan, 'UTF-8'))

def get_sender(msg):
    result = ""
    for char in msg:
        if char == "!":
            break
        if char != ":":
            result += char
    return result

def get_message(msg):
    result = ""
    i = 3
    length = len(msg)
    while i < length:
        result += msg[i] + " "
        i += 1
    result = result.lstrip(':')
    return result
  
def parse_message(msg):
    if len(msg) >= 1:
        msg = msg.split(' ')
        # respond to commands from the chat
        options = {'!forward': command_forward,
                    '!left': command_left,
                    '!right': command_right,
                    '!backward': command_backward,
                    '!test': command_test}
        if msg[0] in options:
            if msg[0] == '!test':
                print("test command received")
            options[msg[0]]()

# just a test
def command_test():
    send_message(CHAN, 'testing some stuff')

# drive robot forward
def command_forward():
    drive(1,50)

# left turn
def command_left():
    drive(1,1)

# right turn
def command_right():
    drive(50,50)

# drive robot in reverse
def command_backward():
    drive(50,1)

# drive robot
def drive(right_value, left_value):
    right = GPIO.PWM(RIGHT_MOTOR, 50)
    left = GPIO.PWM(LEFT_MOTOR, 50)
    right.start(right_value)
    left.start(left_value)
    right.stop()
    left.stop()

def main():
    # login
    send_pass(PASS)
    send_nick(NICK)
    join_channel(CHAN)

    data = ""

    while True:
        # setup raspberry pi GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(RIGHT_MOTOR, GPIO.OUT)
        GPIO.setup(LEFT_MOTOR, GPIO.OUT)
        # read messages
        try:
            data = data+con.recv(1024).decode('UTF-8')
            data_split = re.split(r"[~\r\n]+", data)
            data = data_split.pop()

            for line in data_split:
                line = str.rstrip(line)
                line = str.split(line)

                if len(line) >= 1:
                    if line[0] == 'PING':
                        send_pong(line[1])

                    if line[1] == 'PRIVMSG':
                        sender = get_sender(line[0])
                        message = get_message(line)
                        print(sender + ": " + message)
                        parse_message(message)
                        time.sleep(1);

        except socket.error:
            print("Socket died")

        except socket.timeout:
            print("Socket timeout")

        except KeyboardInterrupt:
            print("Keyboard interrupt caught cleaning up GPIO")
            GPIO.cleanup(RIGHT_MOTOR)
            GPIO.cleanup(LEFT_MOTOR)
            sys.exit(0)


if __name__ == "__main__":
    # connect to twitch
    con = socket.socket()
    con.connect((HOST, PORT))
    main()
