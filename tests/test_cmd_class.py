from seedcli import commands
from unittest import mock


def test_cmdGetClassInitOneArg():
    onTerminal = "seedcli get periph1"
    with mock.patch('sys.argv', onTerminal.split(" ")):
        cmd = commands.Ccmd.fromTerminal()
        assert isinstance(cmd, commands.CcmdGet)
        assert cmd.name == "get"
        assert cmd.args == ["periph1"]
        assert cmd.flags == []


def test_cmdGetClassInitTwoArgs():
    onTerminal = "seedcli get periph1 periph2"
    with mock.patch('sys.argv', onTerminal.split(" ")):
        cmd = commands.Ccmd.fromTerminal()
        assert isinstance(cmd, commands.CcmdGet)
        assert cmd.args == ["periph1", "periph2"]


def test_cmdGetClassInitRejectFlag():
    onTerminal = "seedcli get --someflag periph1"
    with mock.patch('sys.argv', onTerminal.split(" ")):
        cmd = commands.Ccmd.fromTerminal()
        assert isinstance(cmd, commands.CcmdGet)
        assert cmd.args == ["periph1"]
        assert cmd.flags == []


def test_cmdGetClassParse():
    onTerminal = "seedcli get --someflag periph1"
    with mock.patch('sys.argv', onTerminal.split(" ")):
        cmd = commands.Ccmd.fromTerminal()
        assert cmd.parse() == "get periph1"


def test_cmdSetClassInit():
    onTerminal = "seedcli set periph1 100"
    with mock.patch('sys.argv', onTerminal.split(" ")):
        cmd = commands.Ccmd.fromTerminal()
        assert isinstance(cmd, commands.CcmdSet)
        assert cmd.name == "set"
        assert cmd.args == ["periph1", "100"]
        assert cmd.flags == []


def test_cmdSetClassInitMissingValue():
    onTerminal = "seedcli set periph1"
    with mock.patch('sys.argv', onTerminal.split(" ")):
        cmd = commands.Ccmd.fromTerminal()
        assert cmd == None


def test_cmdSetClassParse():
    onTerminal = "seedcli set periph1 100"
    with mock.patch('sys.argv', onTerminal.split(" ")):
        cmd = commands.Ccmd.fromTerminal()
        assert cmd.parse() == "set periph1 100"


def test_cmdSendClassInit():
    onTerminal = 'seedcli send --qspi ./data_small.txt'
    with mock.patch('sys.argv', onTerminal.split(" ")):
        cmd = commands.Ccmd.fromTerminal()
        assert isinstance(cmd, commands.CcmdSend)
        assert cmd.name == "send"
        assert cmd.args == ["./data_small.txt"]
        assert cmd.flags == ["--qspi"]


def test_cmdSendClassAltOrder():
    onTerminal = 'seedcli send ./data_small.txt --sdram'
    with mock.patch('sys.argv', onTerminal.split(" ")):
        cmd = commands.Ccmd.fromTerminal()
        assert cmd.args == ["./data_small.txt"]
        assert cmd.flags == ["--sdram"]


# def test_cmdSendClassParse():
#     onTerminal = 'seedcli send ./data_small.txt --sdram'
#     with mock.patch('sys.argv', onTerminal.split(" ")):
#         cmd = commands.Ccmd.fromTerminal()
#         assert cmd.parse() ==


# def test_cmdSendClass


# def tets_cmdClassParse():
#     cmd = commands.CcmdGet()
#     args = ["periph1"]
#     assert cmd.parse(args) == "get periph1"

#     cmd = commands.CcmdSet()
#     args = ["periph1"]
#     assert cmd.parse(args) == "set periph1"

#     cmd = commands.CcmdSend()
#     args = ["--sdram", "./test.txt"]

test_cmdGetClassInitOneArg()
