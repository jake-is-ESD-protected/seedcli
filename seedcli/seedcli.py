import serial
from serial.tools import list_ports
from time import sleep
import commands
from common import *


class CSeedCli:
    def __init__(self, baudrate=115200, verbose=False) -> None:
        self.verbose = verbose

    def __vPrint(self, printable):
        if self.verbose:
            print(printable)

    def getDaisyPort(self):
        ports = list(list_ports.comports())
        for port in ports:
            if DAISY_HW_IDENTIFIER in port.hwid:
                return port.name
        return None

    def __oneShotTransceive(self, msg: str, waitTime: float = 0.02) -> str:
        self.__vPrint(f"Sending raw string '{msg}'")
        ser = serial.Serial(self.getDaisyPort())
        ser.write(msg.encode())
        sleep(waitTime)
        stat = ser.readline().decode()
        return stat

    def __periodicTransceive(self, msg: str, waitTime: float = 0.02):
        fileSize = len(msg)
        blockI = 0
        blocks = (fileSize / BLOCKSIZE).__ceil__()
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

    def run(self):
        cmd = commands.Ccmd.fromTerminal()
        if not cmd:
            print(f"Error: Uknown command or argument.")
            return
        stat = cli.__oneShotTransceive(cmd.parse())
        self.__vPrint(stat)

        if RESPONSE_OK in stat:
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
    # onTerminal = "seedcli send ./seedcli/tests/data_big.txt --sdram"
    # with mock.patch('sys.argv', onTerminal.split(" ")):
    cli = CSeedCli(verbose=False)
    cli.run()
