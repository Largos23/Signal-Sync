
// -----------------------------------------------------------------------------
//                                   Includes
// -----------------------------------------------------------------------------
#include "rail.h"
#include "sl_simple_button_instances.h"
#include "sl_simple_led_instances.h"
#include "sl_rail_tutorial_downloading_messages_config.h"
#include "app_log.h"
#include "rail.h"
#include "sl_simple_button_instances.h"
#include "sl_simple_led_instances.h"
#include "sl_rail_tutorial_downloading_messages_config.h"
#include "app_log.h"
#include "rail.h"
#include "sl_simple_led_instances.h"
#include "sl_simple_button_instances.h"
#include "sl_rail_tutorial_downloading_messages_config.h"
#include "sl_sleeptimer.h"

#include <stdio.h>
#include <string.h>
// -----------------------------------------------------------------------------
//                              Macros and Typedefs
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
//                          Static Function Declarations
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
//                                Global Variables
// -----------------------------------------------------------------------------
static sl_sleeptimer_timer_handle_t transmit_timer;
// -----------------------------------------------------------------------------
//                                Static Variables
// -----------------------------------------------------------------------------
static uint8_t payload[SL_TUTORIAL_DOWNLOADING_MESSAGES_PAYLOAD_LENGTH] =
{ SL_TUTORIAL_DOWNLOADING_MESSAGES_PAYLOAD_LENGTH - 1, 0x46, 0x0f, 0x03, 0x04,
  0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x00 };


static volatile bool send_packet = false;

// This buffer is not the RAIL RX FIFO, but an application buffer.
static uint8_t rx_buffer[SL_TUTORIAL_DOWNLOADING_MESSAGES_BUFFER_LENGTH];
// -----------------------------------------------------------------------------
//                          Public Function Definitions
// -----------------------------------------------------------------------------
void scheduled_transmit_callback(sl_sleeptimer_timer_handle_t *handle, void *data)
{
  (void)handle;
  (void)data;
  send_packet = true;
}
/******************************************************************************
 * Application state machine, called infinitely
 *****************************************************************************/
void app_process_action(RAIL_Handle_t rail_handle)
{
  sl_sleeptimer_start_periodic_timer_ms(&transmit_timer,
                                        10000, // 10 seconds
                                        scheduled_transmit_callback,
                                        NULL,
                                        0,
                                        0);

  static RAIL_RxPacketHandle_t packet_handle;
  static RAIL_RxPacketInfo_t packet_info;
  static RAIL_RxPacketDetails_t packet_details;

  if (send_packet) {
    send_packet = false;
    // Increment the last byte of the payload
    payload[SL_TUTORIAL_DOWNLOADING_MESSAGES_PAYLOAD_LENGTH - 1]++;
    // If the radio configuration's payload settings doesn't match the
    // SL_TUTORIAL_DOWNLOADING_MESSAGES_PAYLOAD_LENGTH, the FIFO might get
    // corrupt and a FIFO reset may be required in a production quality code
    // before writing anything to it.
    uint16_t size = RAIL_WriteTxFifo(rail_handle,
                                     payload,
                                     SL_TUTORIAL_DOWNLOADING_MESSAGES_PAYLOAD_LENGTH,
                                     false);
    if (size != SL_TUTORIAL_DOWNLOADING_MESSAGES_PAYLOAD_LENGTH) {
      // Turn led1 ON on WriteTxFifo Error
      sl_led_toggle(&sl_led_led1);
    }
    RAIL_Status_t status = RAIL_StartTx(rail_handle,
                                        SL_TUTORIAL_DOWNLOADING_MESSAGES_DEFAULT_CHANNEL,
                                        RAIL_TX_OPTIONS_DEFAULT,
                                        NULL);
    if (status != RAIL_STATUS_NO_ERROR) {
      sl_led_toggle(&sl_led_led1);
    }
  }

  uint32_t ticks = sl_sleeptimer_ms_to_tick(10000);  // 10 seconds
  sl_sleeptimer_start_periodic_timer(&transmit_timer,
                                     ticks,
                                     scheduled_transmit_callback,
                                     NULL,
                                     0,
                                     0);

  packet_handle = RAIL_GetRxPacketInfo(rail_handle,
                                       RAIL_RX_PACKET_HANDLE_OLDEST_COMPLETE,
                                       &packet_info);
  if (packet_handle != RAIL_RX_PACKET_HANDLE_INVALID) {
    RAIL_CopyRxPacket(rx_buffer, &packet_info);
    RAIL_Status_t status =
      RAIL_GetRxPacketDetails(rail_handle, packet_handle, &packet_details);
    if (status != RAIL_STATUS_NO_ERROR) {
      sl_led_toggle(&sl_led_led1);
    }
    status = RAIL_ReleaseRxPacket(rail_handle, packet_handle);
    if (status != RAIL_STATUS_NO_ERROR) {
      sl_led_toggle(&sl_led_led1);
    }

    app_log("RX");
    for (int i = 0; i < packet_info.packetBytes; i++) {
      app_log(" 0x%02X", rx_buffer[i]);
    }
    app_log("; RSSI=%d dBm\n", packet_details.rssi);

  }
}

/******************************************************************************
 * Button callback, called if a Button event occurs
 *****************************************************************************/
void sl_button_on_change(const sl_button_t *handle)
{
  if (sl_button_get_state(handle) == SL_SIMPLE_BUTTON_PRESSED) {
    send_packet = true;
  }
}

/******************************************************************************
 * RAIL callback, called if a RAIL event occurs
 *****************************************************************************/
void sl_rail_util_on_event(RAIL_Handle_t rail_handle, RAIL_Events_t events)
{
  if (events & RAIL_EVENTS_TX_COMPLETION) {
    if (events & RAIL_EVENT_TX_PACKET_SENT) {
      sl_led_toggle(&sl_led_led0);
    } else {
      sl_led_toggle(&sl_led_led1); // all other events in
                                   // RAIL_EVENTS_TX_COMPLETION are errors
    }
  }
  if (events & RAIL_EVENTS_RX_COMPLETION) {
    if (events & RAIL_EVENT_RX_PACKET_RECEIVED) {
      if (RAIL_HoldRxPacket(rail_handle) == RAIL_RX_PACKET_HANDLE_INVALID) {
        sl_led_toggle(&sl_led_led1);
      }
      sl_led_toggle(&sl_led_led0);
    } else {
      sl_led_toggle(&sl_led_led1); // all other events in
                                   // RAIL_EVENTS_RX_COMPLETION are errors
    }
  }
  if (events & RAIL_EVENT_CAL_NEEDED) {
    RAIL_Status_t status = RAIL_Calibrate(rail_handle,
                                          NULL,
                                          RAIL_CAL_ALL_PENDING);
    if (status != RAIL_STATUS_NO_ERROR) {
      sl_led_toggle(&sl_led_led1);
    }
  }
}

// -----------------------------------------------------------------------------
//                          Static Function Definitions
// -----------------------------------------------------------------------------
