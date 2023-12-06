#pragma once

#include "daisy_seed.h"

#define MEM_BLOCK_ERR 0
#define MEM_BLOCK_OK 1
#define MEM_FINISH 2
#define MEM_OVERFLOW 3

#define SDRAM_BUF_SIZE 65536
#define QSPI_BUF_SIZE SDRAM_BUF_SIZE
#define BLOCK_PREFIX_LEN 4
#define BLOCK_POSTFIX_LEN 4
#define BLOCKSIZE_RAW 64
#define BLOCKSIZE_DATA (BLOCKSIZE_RAW - BLOCK_PREFIX_LEN)

#define CRC_POLYNOMIAL 0x8408
#define CRC_INITIAL_VALUE 0xFFFF

#define QSPI_FLASH_PAGE_SIZE 4096

using namespace daisy;

/// @brief Write to the internal buffer in SDRAM.
/// @param buf Data source buffer.
/// @param len Length of data to write.
/// @param args Optional args.
/// @return MEM status flag.
uint8_t memSdramWrite(void *buf, uint32_t len, void *args);

/// @brief Write to the external flash buffer over QSPI.
/// @param buf Data source buffer.
/// @param len Length of data to write.
/// @param args Optional args.
/// @return MEM status flag.
uint8_t memQspiWrite(void *buf, uint32_t len, void *args);

/// @brief Check if an incoming data frame is an EOF frame.
/// @param buf Buffer to check.
/// @return truth of statement.
bool memIsEOF(void *buf);

/// @brief Calculate CRC-value from data buffer.
/// @param data Data buffer.
/// @param len Length of data.
/// @return CRC16 value.
uint16_t memCrc16(const uint8_t *data, uint32_t len);

/// @brief Erase (prime) the external flash memory.
/// @param mem Start address of memory.
/// @param len Length of data.
void __memEraseQspiFlash(uint8_t *mem, uint32_t len);

/// @brief Write to external flash memory.
/// @param start Start address of memory.
/// @param len Length of buffer.
/// @param content Buffer data to write to memory.
void __memWriteQspiFlash(uint32_t start, uint32_t len, uint8_t *content);
