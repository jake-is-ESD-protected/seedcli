#include "cli.hpp"
#include "hal.hpp"
#include "mem.hpp"
#include "transientDSP.hpp"
#include "ui.hpp"
#include "ai.h"
#include "af.h"

static uint8_t rxBuf[CLI_RX_BUF_SIZE] = {0};
static cli_state_t state = CLI_STATE_idle;

void cliInit(void)
{
    hw.usb_handle.Init(UsbHandle::FS_INTERNAL);
    System::Delay(1000);
    hw.usb_handle.SetReceiveCallback(cliRXCallback, UsbHandle::FS_INTERNAL);
    System::Delay(1000);
}

void cliRXCallback(uint8_t *buf, uint32_t *len)
{
    if (state == CLI_STATE_idle)
        halStopAudio();
    cliServer(buf, len);
    if (state == CLI_STATE_idle)
        halStartAudio();
}

void cliPrintBuf(uint8_t *buf, uint32_t len)
{
    hw.usb_handle.TransmitInternal(buf, len);
}

void cliPrintStr(const char *type, const char *str)
{
    char txBuf[CLI_TX_BUF_SIZE] = {0};
    if (str == NULL)
    {
        sprintf(txBuf, "%s %s%s", CLI_PREFIX, type, LINE_ENDING);
    }
    else
    {
        sprintf(txBuf, "%s %s: %s%s", CLI_PREFIX, type, str, LINE_ENDING);
    }
    cliPrintBuf((uint8_t *)txBuf, strlen(txBuf));
}

uint8_t cliParse(void *cmd, uint32_t len, void *args)
{
    char *msg = (char *)cmd;
    char *mainCmd = strtok(msg, " ");

    if (!strcmp(mainCmd, CMD_GET))
    {
        char *sub_cmd = strtok(NULL, " ");
        if (!strcmp(sub_cmd, "af"))
        {
            char *id_cmd = strtok(NULL, " ");

            if (id_cmd == NULL)
            {
                cliPrintStr(RESPONSE_ERR, "ID missing");
            }

            char *song_id_cmd = strtok(NULL, " ");

            if (song_id_cmd == NULL)
            {
                cliPrintStr(RESPONSE_ERR, "Song ID missing");
            }

            char buff[200] = {0};
            char b_knob_attack[8] = {0};
            char b_knob_sustain[8] = {0};
            char b_tau1[16] = {0};
            char b_tau2[16] = {0};
            char b_tau3[16] = {0};
            char b_tau4[16] = {0};

            formatFloat((float)KnobAttack.getValue(), 4, b_knob_attack);
            formatFloat((float)KnobSustain.getValue(), 4, b_knob_sustain);

            formatFloat((float)attackSlowF.get_attack(), 4, b_tau1);
            formatFloat((float)attackSlowF.get_release(), 4, b_tau2);
            formatFloat((float)sustainSlowF.get_release(), 4, b_tau3);
            formatFloat((float)sustainFastF.get_release(), 4, b_tau4);

            sprintf(buff, "%s, %s, %s, %s, %s, %s, %s, %s", id_cmd, song_id_cmd, b_knob_attack, b_knob_sustain, b_tau1, b_tau2, b_tau3, b_tau4);
            cliPrintStr(RESPONSE_OK, buff);
        }
        else if(!strcmp(sub_cmd, "ai")){
            char buff[64] = {0};
            char b_tau1[16] = {0};
            char b_tau2[16] = {0};
            formatFloat(aiGetATTACK_T1(), 4, b_tau1);
            formatFloat(aiGetSUSTAIN_T1(), 4, b_tau2);
            sprintf(buff, "%s, %s", b_tau1, b_tau2);
            cliPrintStr(RESPONSE_OK, buff);
        }
        else if (!strcmp(sub_cmd, "time")){
            char buff[64] = {0};
            sprintf(buff, "af: %d ms, ai: %d ms", (int)afGetTimeAF(), (int)aiGetTimeInf());
            cliPrintStr(RESPONSE_OK, buff);
        }
        else
        {
            cliPrintStr(RESPONSE_ERR, "Getter not yet implemented.");
        }
        state = CLI_STATE_idle;
    }
    else if (!strcmp(mainCmd, CMD_RESET))
    {
        resetShiftLayer();
        cliPrintStr(RESPONSE_OK, "Shift layer has been reset.");
        state = CLI_STATE_idle;
    }
    else if (!strcmp(mainCmd, CMD_SET))
    {
        cliPrintStr(RESPONSE_ERR, "Setter not yet implemented.");
        state = CLI_STATE_idle;
    }
    else if (!strcmp(mainCmd, CMD_SEND))
    {
        char *arg = strtok(NULL, " ");
        if (!strcmp(arg, CMD_SEND_FLAG_SDRAM))
        {
            state = CLI_STATE_stream_sdram;
            cliPrintStr(RESPONSE_RDY, "Awaiting data transfer to SDRAM...");
        }
        else
        {
            state = CLI_STATE_stream_qspi;
            cliPrintStr(RESPONSE_RDY, "Awaiting data transfer to QSPI...");
        }
    }
    else
    {
        /// TODO: Something went wrong
        char txBuf[CLI_TX_BUF_SIZE] = {0};
        sprintf(txBuf, "Parse error: unknown command <%s>", mainCmd);
        cliPrintStr(RESPONSE_ERR, txBuf);
    }
    return CLI_STAT_OK;
}

uint8_t cliErrHandler(void *err, uint32_t len, void *args)
{
    return CLI_STAT_OK;
}

void cliServer(uint8_t *buf, uint32_t *len)
{
    uint32_t i = 0;
    while (i < *len && i < CLI_RX_BUF_SIZE)
    {
        rxBuf[i] = buf[i];
        i++;
    }
    static consumer consFunction = NULL;
    switch (state)
    {
    case CLI_STATE_idle:
        consFunction = cliParse;
        break;
    case CLI_STATE_stream_sdram:
        consFunction = memSdramWrite;
        break;
    case CLI_STATE_stream_qspi:
        consFunction = memQspiWrite;
        break;
    default:
        consFunction = cliErrHandler;
        break;
    }
    uint16_t argReturn = 0;
    uint8_t stat = consFunction((void *)rxBuf, *len, (void *)&argReturn);
    if (stat == MEM_BLOCK_OK)
    {
        cliPrintStr(RESPONSE_OK, NULL);
    }
    if (stat == MEM_FINISH)
    {
        char txBuf[CLI_TX_BUF_SIZE] = {0};
        sprintf(txBuf, "Transmission done. CRC: %d", argReturn);
        cliPrintStr(RESPONSE_FNSH, txBuf);
        state = CLI_STATE_idle;
    }
    if (stat == CLI_STAT_OK)
    {
        for (int i = 0; i < CLI_RX_BUF_SIZE; i++)
        {
            rxBuf[i] = 0;
        }
    }
    // TODO: catch mem overflow and default err
}

void formatFloat(float value, int decimal_places, char *out_str)
{
    int int_part = (int)value;          // Extract integer part
    float frac_part = value - int_part; // Extract fractional part

    // Handle negative sign if needed
    if (int_part < 0)
    {
        int_part = -int_part;
        *out_str++ = '-';
    }

    // Convert integer part to string
    int int_digits = sprintf(out_str, "%d", int_part);
    out_str += int_digits;

    // Add decimal point if necessary
    if (decimal_places > 0)
    {
        *out_str++ = '.';

        // Multiply fractional part to get desired precision
        frac_part *= pow(10, decimal_places);

        // Convert fractional part (now an integer) to string
        sprintf(out_str, "%d", (int)frac_part);
    }
}