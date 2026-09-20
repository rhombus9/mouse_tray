# M5 Nano battery query:
#
# SET_FEATURE / Report ID 0x51:
#   51 06 00 00 00 00 ...
# or 
#   51 03 00 00 00 00 ...
#
# followed by GET_FEATURE / Report ID 0x51.
#
# Confirmed responses:
#
# 47%:
#   51 06 01 00 8A 24 3B FF 00 01 09 2F 01 00 01 ...
#
# 40%:
#   51 06 01 00 8A 24 3B FF 00 01 09 28 00 00 01 ...
#
# Byte 11 is the battery percentage.
# When SET_FEATURE is 51 03 ...
# Byte  7 is the charging state(opposite).
#
# Charging:                          []
#   51 06 01 00 8A 24 3B FF 00 01 01 64 01 00 01 ...
# Not charging:
#   51 06 01 00 8A 24 3B FF 00 01 09 64 00 00 01 ...
#
# Charging:              []          []
#   51 03 01 8A 24 3B FF 00 00 01 01 64 01 00 01 ...
# Not charging:          !!
#   51 03 01 8A 24 3B FF 01 00 01 09 64 00 00 01 ...

from ...battery import BatteryStatus
from ..driver import MouseModel, register
from ..hid import HidDriver

import logging

log = logging.getLogger(__name__)


@register
class HansungDriver(HidDriver):
    vendor = "Hansung"

    models = [
        MouseModel(
            "Hansung M5 Nano OfficeMaster",
            0x248A,
            0xFF3C,
            0xFF3C,
            interface=1,
        )
    ]

    def read_status(self) -> BatteryStatus:
        
        res = self._transact(
            [0x51, 0x03, 0x00],
            read_length=21,
            feature=True,
        )

        if res is None or len(res) < 12:
            return BatteryStatus.absent()

        percent = res[11]
        charging = not(bool(res[7]))

        response=" ".join(f"{x:02X}" for x in res)

        if getattr(self, "_last_percent", None) != percent:
            log.info("%s battery=%d%%", self.name, percent)
            self._last_percent = percent

        if getattr(self, "_last_response", None) != response:
            log.debug("%s battery report: %s", self.name, response)
            self._last_response = response

        if getattr(self, "_last_charging", None) != charging:
            log.info("%s battery charging: %s", self.name, charging)
            self._last_charging = charging
            # This mouse doesn't report its battery percentage while charging, so return full=True once if the battery is at 100% when charging stops.
            if charging==False and percent==100:
                return BatteryStatus(
                    present=True,
                    percent=percent,
                    charging=charging,
                    full=True,
                )

        return BatteryStatus(
            present=True,
            percent=percent,
            charging=charging,
            full=False,
        )
