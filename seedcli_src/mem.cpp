#include "mem.hpp"
#include "cli.hpp"
#include "hal.hpp"

static char DSY_SDRAM_BSS sdramBuf[SDRAM_BUF_SIZE];
char DSY_QSPI_BSS qspiBuf[QSPI_BUF_SIZE];

uint8_t memSdramWrite(void *buf, uint32_t len, void *args)
{
    static uint32_t i = 0;
    if (memIsEOF(buf))
    {
        uint16_t crc = memCrc16(&((const uint8_t *)sdramBuf)[0], i * BLOCKSIZE_DATA);
        memcpy((void *)&(sdramBuf[i * BLOCKSIZE_DATA]), (void *)&crc, sizeof(crc));
        *(uint16_t *)args = crc;
        i = 0;
        return MEM_FINISH;
    }
    char *dataPos = &((char *)buf)[BLOCK_PREFIX_LEN];
    memcpy((void *)&(sdramBuf[i * BLOCKSIZE_DATA]), dataPos, BLOCKSIZE_DATA);
    i++;
    if ((i * BLOCKSIZE_DATA) >= SDRAM_BUF_SIZE)
    {
        i = 0;
        return MEM_OVERFLOW;
    }
    return MEM_BLOCK_OK;
}

uint8_t memQspiWrite(void *buf, uint32_t len, void *args)
{
    static uint32_t i = 0;
    uint8_t stat = memSdramWrite(buf, len, args);
    if (stat == MEM_FINISH)
    {
        size_t startAddr = (size_t)qspiBuf;
        __memEraseQspiFlash((uint8_t *)qspiBuf, (i * BLOCKSIZE_DATA));
        __memWriteQspiFlash(startAddr, (i * BLOCKSIZE_DATA), (uint8_t *)sdramBuf);
        i = 0;
    }
    i++;
    return stat;
}

bool memIsEOF(void *buf)
{
    char blockIndicator[BLOCK_PREFIX_LEN + 1] = {0};
    strncpy(blockIndicator, (char *)buf, BLOCK_PREFIX_LEN);
    if (!strcmp(blockIndicator, EOF_FLAG))
    {
        return true;
    }
    return false;
}

uint16_t memCrc16(const uint8_t *data, uint32_t len)
{
    uint16_t crc = CRC_INITIAL_VALUE;
    uint32_t i, j;
    for (i = 0; i < len; ++i)
    {
        crc ^= (uint16_t)data[i];
        for (j = 0; j < 8; ++j)
        {
            if (crc & 1)
            {
                crc = (crc >> 1) ^ CRC_POLYNOMIAL;
            }
            else
            {
                crc >>= 1;
            }
        }
    }
    return crc;
}

void __memEraseQspiFlash(uint8_t *mem, uint32_t len)
{
    uint32_t startAddr = (uint32_t)mem;
    uint32_t padLen = ((len + QSPI_FLASH_PAGE_SIZE - 1) / QSPI_FLASH_PAGE_SIZE) * QSPI_FLASH_PAGE_SIZE;
    hw.qspi.Erase(startAddr, startAddr + padLen);
}

void __memWriteQspiFlash(uint32_t start, uint32_t len, uint8_t *content)
{
    uint32_t padLen = ((len + QSPI_FLASH_PAGE_SIZE - 1) / QSPI_FLASH_PAGE_SIZE) * QSPI_FLASH_PAGE_SIZE;
    hw.qspi.Write(start, padLen, content);
}