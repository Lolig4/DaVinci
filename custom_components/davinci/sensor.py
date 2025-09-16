"""DaVinci Timetable sensor platform."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import aiohttp

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import ATTRIBUTION, BLOCK_GROUP, HOST, PASS, USER

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up DaVinci sensor."""
    async_add_entities([TimetableData(hass, entry)])


async def async_get_davinci_data(hostname: str, username: str, password: str) -> dict[str, Any]:
    """Get station data from INSA API asynchronously."""
    payload = {
        "content": "json",
        "username": username,
        "key": hashlib.md5(password.encode()).hexdigest(),
    }

    url = f"http://{hostname}/daVinciIS.dll"

    async with aiohttp.ClientSession() as session, session.get(url, params=payload, timeout=5) as response:
        response.raise_for_status()
        return await response.json()


def get_current_timetable(data, block_group):
    """Return the timetable for the current week."""
    today = dt_util.now().date()
    current_year, current_week, current_weekday = today.isocalendar()
    current_time = dt_util.now().strftime("%H%M")

    def get_block(start_time):
        blocks = {
            "0800": 1,
            "0955": 2,
            "1155": 3,
            "1340": 4
        }
        return blocks.get(start_time)

    def time_in_block(start, end, now):
        return start <= now < end

    def get_next_block(blocks_today, now):
        for block in blocks_today:
            if now < block["start"]:
                return block
        return None

    timetable = []
    blocks_today = []

    # Collect all blocks for the current week
    for lesson in data["result"]["displaySchedule"]["lessonTimes"]:
        for date in lesson["dates"]:
            formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            dt = dt_util.parse_datetime(f"{formatted_date}T00:00:00").date()
            year, week, weekday = dt.isocalendar()
            block = get_block(lesson["startTime"])
            subject = lesson["subjectCode"]
            # Filter by block_group
            if block_group == 1 and subject.endswith("/2"):
                continue
            if block_group == 2 and subject.endswith("/1"):
                continue
            if year == current_year and week == current_week and weekday in range(1, 6) and block in range(1, 5):
                block_info = {
                    "subject": subject,
                    "date": date,
                    "weekday": weekday,
                    "block": block,
                    "room": lesson["roomCodes"][0] if lesson.get("roomCodes") else None,
                    "teacher": lesson["teacherCodes"][0] if lesson.get("teacherCodes") else None,
                    "start": lesson["startTime"],
                    "end": lesson["endTime"],
                    "current": False
                }
                timetable.append(block_info)
                if weekday == current_weekday:
                    blocks_today.append(block_info)

    # Sort today's blocks by start time
    blocks_today.sort(key=lambda x: x["start"])

    # Mark the current or next block for today
    current_found = False
    for block_info in blocks_today:
        is_current = time_in_block(block_info["start"], block_info["end"], current_time)
        if is_current and not current_found:
            current_found = True
            block_info["current"] = True
        else:
            block_info["current"] = False

    # If no current block, mark the next block for today
    if not current_found and blocks_today:
        next_block = get_next_block(blocks_today, current_time)
        if next_block:
            next_block["current"] = True

    # If no block left today, mark the first block of the next day
    if not current_found and (not get_next_block(blocks_today, current_time)):
        for offset in range(1, 6):
            next_day = today + dt_util.dt.timedelta(days=offset)
            _next_year, _next_week, next_weekday = next_day.isocalendar()
            next_day_blocks = [
                block_info for block_info in timetable
                if block_info["weekday"] == next_weekday and block_info["date"] == next_day.strftime("%Y%m%d")
            ]
            if next_day_blocks:
                first_block = min(next_day_blocks, key=lambda x: x["block"])
                first_block["current"] = True
                break

    # Remove helper fields
    for block in timetable:
        block.pop("start", None)
        block.pop("end", None)

    return timetable


class TimetableData(SensorEntity):
    """Representation of a sensor that fetches timetable data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._entry = config_entry
        self._hostname = config_entry.data[HOST]
        self._username = config_entry.data[USER]
        self._password = config_entry.data[PASS]
        self._block_group = config_entry.data[BLOCK_GROUP]

        # Set entity properties
        self._attr_name = "DaVinci Timetable"
        self._attr_unique_id = f"{config_entry.entry_id}-timetable"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {
            "latest_update": None,
            "data": {},
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    async def async_update(self) -> None:
        """Fetch new timetable data."""
        try:
            data = await async_get_davinci_data(self._hostname, self._username, self._password)
            timetable = get_current_timetable(data, self._block_group)

            # Reorganize data by weekdays
            weekday_data = {}
            for block in timetable:
                weekday = block.get("weekday")
                if weekday not in weekday_data:
                    weekday_data[weekday] = []
                weekday_data[weekday].append({
                    "block": block.get("block"),
                    "subject": block.get("subject"),
                    "room": block.get("room"),
                    "teacher": block.get("teacher"),
                    "current": block.get("current"),
                })

            # Sort blocks within each day by block number
            for day_blocks in weekday_data.values():
                day_blocks.sort(key=lambda x: x["block"] if isinstance(x["block"], int) else 0)

            # Find the maximum number of blocks across all days
            max_blocks = max((len(blocks) for blocks in weekday_data.values()), default=0)

            # Fill missing blocks for each day to match max_blocks
            for weekday_num in range(1, 6):  # Monday=1 to Friday=5
                if weekday_num not in weekday_data:
                    weekday_data[weekday_num] = []

                current_blocks = len(weekday_data[weekday_num])
                missing_blocks = max_blocks - current_blocks

                # Add empty blocks to fill the gap
                for _ in range(missing_blocks):
                    weekday_data[weekday_num].append({
                        "block": None,
                        "subject": "",
                        "room": "",
                        "teacher": "",
                        "current": False,
                    })

            # Build final attributes
            attributes = weekday_data.copy()
            attributes["latest_update"] = dt_util.now().strftime("%H:%M:%S")
            attributes[ATTR_ATTRIBUTION] = ATTRIBUTION

            self._attr_native_value = "Updated"
            self._attr_extra_state_attributes.update(attributes)
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.debug("Failed to update timetable data: %s", err)
            self._attr_native_value = None
