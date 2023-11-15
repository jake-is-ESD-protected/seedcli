import sys
import os
from common import *


class Ccmd:
    def __init__(self, name: str, args: list[str]):
        self.name = name
        self.args = args

    def stripFlags(self, args: list[str]) -> list[str]:
        if not isinstance(args, list):
            args = [args]
        flags = [arg for arg in args if arg.startswith(FLAGPREFIX)]
        args = [arg for arg in args if not arg.startswith(FLAGPREFIX)]
        return args, flags

    @staticmethod
    def sanitizeFlags(flags: list[str], knownFlags: list[str]):
        for flag in flags:
            if flag not in knownFlags:
                print(f"Unsupported flag <{flag}>.")
                return []
        return flags

    @classmethod
    def fromTerminal(cls):  # this is a factory
        if len(sys.argv) < 3:  # argv[0] is "seedcli", argv[1] is "name"
            print(f"Expected a name, argument or flag")
            return None
        name = sys.argv[1]
        args = sys.argv[2:]
        args, flags = cls.stripFlags(cls, args)
        if name == CMD_GET:
            return CcmdGet.getInstance(args, flags)
        elif name == CMD_SET:
            return CcmdSet.getInstance(args, flags)
        elif name == CMD_SEND:
            return CcmdSend.getInstance(args, flags)
        else:
            print(f"Unsupported command name: {name}")


class CcmdGet(Ccmd):
    def __init__(self, args: list[str], flags: list[str]):
        self.flags = flags
        super().__init__(CMD_GET, args)

    @classmethod
    def getInstance(cls, args, flags):
        knownFlags = []
        flags = cls.sanitizeFlags(flags, knownFlags)
        return cls(args, flags)

    def parse(self):
        cmdStr = self.name + " " + " ".join(self.args)
        return cmdStr


class CcmdSet(Ccmd):
    def __init__(self, args: list[str], flags: list[str]):
        self.flags = flags
        super().__init__(CMD_SET, args)

    @classmethod
    def getInstance(cls, args, flags):
        if len(args) != 2:
            print(
                f"<{CMD_SET}> takes exactly two argument names: seedcli {CMD_SET} <target> <value>")
            return None
        knownFlags = []
        flags = cls.sanitizeFlags(flags, knownFlags)
        return cls(args, flags)

    def parse(self):
        cmdStr = self.name + " " + " ".join(self.args)
        return cmdStr


class CcmdSend(Ccmd):
    def __init__(self, args: list[str], flags: list[str]):
        self.flags = flags
        self.targetFile = args[0]  # only one file at a time supported
        super().__init__(CMD_SEND, args)

    @classmethod
    def getInstance(cls, args, flags):
        if not os.path.exists(args[0]):
            print(f"File <{args[0]}> does not exist!")
            return None
        knownFlags = [CMD_SEND_FLAG_SDRAM, CMD_SEND_FLAG_QSPI]
        flags = cls.sanitizeFlags(flags, knownFlags)
        if flags == []:
            flags = [CMD_SEND_FLAG_SDRAM]
        return cls(args, flags)

    def parse(self):
        try:
            with open(self.targetFile, "rb") as f:
                data = f.read()
        except:
            print(f"File <{self.targetFile}> does not exist!")
            return None
        return f"{self.name} {len(data)}"


class CcmdData(Ccmd):
    def __init__(self, args: str):
        super().__init__(CMD_DATA, [args])
        self.data = self.args[0].encode()

    @classmethod
    def getInstance(cls, data):
        return cls(data)

    def pad(self):
        size = len(self.data)
        padLen = BLOCKSIZE - size
        payload = self.name.encode() + self.data
        payload += (padLen * PAD_BYTE).encode()
        return payload

    def parse(self):
        return self.pad()
