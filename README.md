# 🌻seedcli💻
**Command line interface for the Electrosmith Daisy Seed board.**

## ↗️ About
Sometimes you need to control your Daisy Seed without external hardware or you need to fetch some data for automated testing. You might even upload some stuff like audio files or neural network weights onto it. Whatever it is, it is very useful to be able to interact with your Seed backend during runtime.

## ⚙️ Installation
Set up a Daisy Seed project as described on their getting started wiki. Download this repo into it with
```
git clone https://github.com/jake-is-ESD-protected/seedcli
```
And append 
- `CPP_SOURCES += seedcli/seedcli_src/cli.cpp`
- `CPP_SOURCES += seedcli/seedcli_src/mem.cpp`
- `-I./seedcli/seedcli_src`  
to your `makefile` like this:
```makefile
... other cpp-sources
...
CPP_SOURCES += seedcli/seedcli_src/cli.cpp
CPP_SOURCES += seedcli/seedcli_src/mem.cpp
...
... other cpp-sources

C_INCLUDES += \
...
-I other includes...
...
-I./seedcli/seedcli_src \
...
```

> ⚠️ Be sure that you have **python 3** installed, otherwise the client side code (on your machine) won't work!

## Usage  
Since we can't know what you intend to do with your CLI, we only provide very simple functionalities that you have to populate properly in order to perform what you want. The CLI works by parsing commands from the command line and passing them to a python script which sanitizes them. They are then sent to the Seed with `pyserial`, which automatically identifies the port the seed is connected to. These are the basic features:

- `get <name>`: get the value of whatever you implemented in the `cli.cpp` for the getter function.
- `set <name> <value>`: set the value of whatever you implemented in the `cli.cpp` for the setter function.
- `send <file> [--sdram, --qspi]`: Upload a file to the Seed either to the volatile SDRAM or persistent external QSPI-flash memory.

When working from your base directory, a CLI call for uploading a wav file might look like this:
```
cd seedcli
./seedcli.bat send bassdrop.wav --qspi  # windows
./seedcli.sh send bassdrop.wav --qspi   # linux
```
