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
        DAISY_HW_IDENTIFIER = "VID:PID=0483:5740"
        ports = list(list_ports.comports())
        for port in ports:
            if DAISY_HW_IDENTIFIER in port.hwid:
                self.__vPrint(
                    f"Found Daisy Seed ({port.hwid}) on port {port.name}")
                return port.name
        return None

    def __oneShotTransceive(self, msg: str, waitTime: float = 0.02) -> str:
        self.__vPrint(f"Sending raw string '{msg}'")
        ser = serial.Serial(self.getDaisyPort())
        ser.write(msg.encode())
        sleep(waitTime)
        stat = ser.readline().decode()
        self.__vPrint(f"Received {stat} from Seed")
        return stat

    def __periodicTransceive(self, msg: str, waitTime: float = 0.02):
        fileSize = len(msg)
        fullBlockSize = BLOCKSIZE + len(CMD_DATA)
        blockI = 0
        blocks = (fileSize / fullBlockSize).__ceil__()
        ser = serial.Serial(self.getDaisyPort())
        while (blockI < blocks):
            self.__vPrint(
                f"writing {BLOCKSIZE + len(CMD_DATA)} bytes to {ser.port}: Block #{blockI+1}")
            split = msg[blockI*BLOCKSIZE:(blockI+1)*BLOCKSIZE]
            cmdData = commands.CcmdData.getInstance(split)
            self.__vPrint(cmdData.parse())
            ser.write(cmdData.parse())
            sleep(waitTime)
            stat = ser.readline().decode()
            self.__vPrint(stat)
            if stat != CLI_PREFIX + " " + RESPONSE_OK:
                return stat
            blockI += 1
        # TODO: CRC
        return CLI_PREFIX + " " + RESPONSE_OK

    def run(self):
        cmd = commands.Ccmd.fromTerminal()
        if not cmd:
            print(f"Error: Uknown command or argument.")
            return
        stat = cli.__oneShotTransceive(cmd.parse())
        self.__vPrint(stat)
        if stat == CLI_PREFIX + " " + RESPONSE_OK:
            return
        if stat.startswith(CLI_PREFIX + " " + RESPONSE_ERR):
            print(f"Error: Seed returned <{stat}>")
            return
        with open(cmd.targetFile, "r") as f:
            data = f.read()
        stat = self.__periodicTransceive(data)
        self.__vPrint(stat)
        if stat != CLI_PREFIX + " " + RESPONSE_OK:
            print(f"Error: A block transfer failed")
            return
        cmdData = commands.CcmdData.getInstance(EOF_FLAG)
        stat = self.__oneShotTransceive(cmdData.parse())
        self.__vPrint(stat)
        if stat != CLI_PREFIX + " " + RESPONSE_FNSH:
            print("Seed did not terminate connection with properly!")
            return


if __name__ == "__main__":
    from unittest import mock
    onTerminal = "seedcli send ./tests/data_small.txt --sdram"
    with mock.patch('sys.argv', onTerminal.split(" ")):
        cli = CSeedCli(verbose=True)
        cli.run()
