import serial
from serial.tools import list_ports
from time import sleep
import commands
from common import *
import numpy as np
import os
import math


class CSeedCli:
    def __init__(self, baudrate=115200, verbose=False) -> None:
        self.verbose = verbose
        self.given_port = None

    def __vPrint(self, printable):
        if self.verbose:
            print(printable)

    def getDaisyPort(self):
        if self.given_port:
            self.__vPrint(f"Using port {self.given_port}")
            return self.given_port
        ports = list(list_ports.comports())
        for port in ports:
            if DAISY_HW_IDENTIFIER in port.hwid:
                self.__vPrint(f"Using port {port.name}")
                return port.name
        return None



    def __oneShotTransceive(self, msg: str, waitTime: float = 0.02) -> str:
        self.__vPrint(f"Sending raw string '{msg}'")
        port = self.getDaisyPort()
        if not port:
            print("Could not find Daisy Seed!")
            return None
        ser = serial.Serial(port)
        print(ser.port)
        ser.write(msg.encode())
        sleep(waitTime)
        stat = ser.readline().decode()

        if(msg.startswith("get af")):
            measurmentId = stat[12:].split(",")[0]
            songId = stat[12:].split(",")[1].lstrip()

            with open("AITD_Dataset.csv", "a+") as file:
                s = ','.join(map(str, stat.split(":")[2:]))
                s = s.lstrip()
                file.write(s)

            self.__vPrint("MeasurmentId: " + measurmentId + " SongId: " + songId)

        return stat

    def __periodicTransceive(self, msg: str, waitTime: float = 0.02):
        fileSize = len(msg)
        blockI = 0
        blocks = np.ceil(fileSize / BLOCKSIZE)
        ser = serial.Serial(self.getDaisyPort())
        crcData = bytes()
        while (blockI < blocks):
            self.__vPrint(
                f"writing {BLOCKSIZE + len(CMD_DATA)} bytes to {ser.port}: Block #{blockI+1}/{blocks}:")
            split = msg[blockI*BLOCKSIZE:(blockI+1)*BLOCKSIZE]
            cmdData = commands.CcmdData.getInstance(split)
            dataRaw = cmdData.parse().encode()
            self.__vPrint(dataRaw)
            crcData += dataRaw[len(CMD_DATA):]
            ser.write(dataRaw)
            sleep(waitTime)
            stat = ser.readline().decode()
            stat = stat.replace("\n", "").replace("\r", "")
            if stat != (CLI_PREFIX + " " + RESPONSE_OK):
                print(f"Early exit error: {stat}")
                return stat
            self.__vPrint(stat)
            blockI += 1
            self.progressBar(0, blocks)
        crc = self.crc16(crcData)
        return CLI_PREFIX + " " + RESPONSE_OK, crc

    def crc16(self, data):
        crc = CRC_INITIAL_VALUE
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc >> 1) ^ CRC_POLYNOMIAL if crc & 1 else crc >> 1
        return crc & 0xFFFF

    def progressBar(self, min, max):
        if self.verbose:
            return
        print(f"{'█' * int(100/(max-min))}", end="", flush=True)

    def drawPotis(self, t1, t2):
        radius = 10
        diameter = 2 * radius
        min_value = 0
        max_value = 1
        space_between_gauges = 30

        def normalize_value(value):
            return (value - min_value) / (max_value - min_value)

        def map_angle(normalized_value):
            return 240 - normalized_value * 300

        def create_gauge_array():
            return [[' ' for _ in range(diameter * 4 + space_between_gauges + 2)] for _ in range(diameter + 1)]

        def draw_circle(gauge, offset):
            for y in range(diameter + 1):
                for x in range(diameter * 2 + 1):
                    dx = (x - radius * 2) / 2  # Adjust the x-coordinate for aspect ratio
                    dy = y - radius
                    distance = math.sqrt(dx * dx + dy * dy)
                    theta = math.atan2(dy, dx)
                    theta_degrees = math.degrees(theta)
                    if theta_degrees < 0:
                        theta_degrees += 360
                    theta_degrees = (theta_degrees + 180) % 360  # Adjust for terminal coordinate
                    if abs(distance - radius) < 1:  # Adjust thickness of the circle line
                        if theta_degrees <= 240 or theta_degrees >= 300:
                            gauge[y][x + offset] = '#'

        def draw_needle(gauge, angle, offset):
            cx, cy = radius * 2, radius
            for r in range(radius):
                nx = int(cx + r * math.cos(angle) * 2) + offset  # Adjust for aspect ratio
                ny = int(cy - r * math.sin(angle))
                if 0 <= nx < diameter * 4 + space_between_gauges + 2 and 0 <= ny < diameter + 1:
                    gauge[ny][nx] = '*'

        # Create a 2D array to represent both gauges
        gauge = create_gauge_array()

        # First gauge
        normalized_value1 = normalize_value(t1)
        angle_degrees1 = map_angle(normalized_value1)
        angle1 = math.radians(angle_degrees1)
        draw_circle(gauge, 0)
        draw_needle(gauge, angle1, 0)

        # Second gauge
        normalized_value2 = normalize_value(t2)
        angle_degrees2 = map_angle(normalized_value2)
        angle2 = math.radians(angle_degrees2)
        draw_circle(gauge, diameter * 2 + space_between_gauges + 1)
        draw_needle(gauge, angle2, diameter * 2 + space_between_gauges + 1)

        # Print the gauges
        for row in gauge:
            print(''.join(row))

    def run(self):
        cmd = commands.Ccmd.fromTerminal()
        if not cmd:
            print(f"Error: Uknown command or argument.")
            return
        if CMD_PORT_SPECIFIED_FLAG in cmd.flags:
            idx = cmd.flags.index(CMD_PORT_SPECIFIED_FLAG) + 1
            cmd.flags.remove(CMD_PORT_SPECIFIED_FLAG)
            port = cmd.args[idx]
            cmd.args.remove(port)
            self.given_port = port
        stat = cli.__oneShotTransceive(cmd.parse())
        self.__vPrint(stat)

        if RESPONSE_OK in stat:
            if "ai" in cmd.args:    # AI-TD CLI AI output visualizer for demo
                temp = stat.split()
                t1 = temp[-2][:-1]
                t2 = temp[-1]
                self.drawPotis(float(t1), float(t2))
            return
        if RESPONSE_ERR in stat:
            print(f"Error: Seed returned {stat}")
            return
        with open(cmd.targetFile, "r") as f:
            data = f.read()
        print(f"Uploading <{f.name}> to Seed...")
        stat, crc = self.__periodicTransceive(data)
        if RESPONSE_OK not in stat:
            print(f"Error: A block transfer failed")
            return

        cmdStop = commands.CcmdStop.getInstance()
        stat = self.__oneShotTransceive(cmdStop.parse())
        self.__vPrint(stat)
        if RESPONSE_FNSH not in stat:
            print("Seed did not terminate connection with properly!")
            return
        self.__vPrint(f"CRC checksum on client side: {crc}")
        if not stat.replace("\n", "").replace("\r", "").endswith(str(crc)):
            print("CRC checksums do not match, data might be corrupted!")
            return
        print()
        print(stat)


if __name__ == "__main__":
    # from unittest import mock
    # onTerminal = "seedcli get x --p COM1"
    # with mock.patch('sys.argv', onTerminal.split(" ")):
    cli = CSeedCli(verbose=True)
    cli.run()
