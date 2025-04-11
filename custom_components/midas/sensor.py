"""Sensor platform for the MIDAS integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import MidasDataUpdateCoordinator

if TYPE_CHECKING:
    from collections.abc import Callable
    from decimal import Decimal

    from california_midasapi.types import RateInfo, ValueInfoItem
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .data import IntegrationMidasConfigEntry

DATA_RATE_NAME = "rate_name"
DATA_RATE_TYPE = "rate_type"
DATA_RATE_URL = "rate_url"
DATA_TARIFF_NAME = "tariff_name"
DATA_START_TIME = "start_time"
DATA_END_TIME = "end_time"


@dataclass(frozen=True, kw_only=True)
class MidasSensorEntityDescription(SensorEntityDescription):
    """Describes MIDAS sensors."""

    tariffs_fn: Callable[[RateInfo], list[ValueInfoItem]] = (
        lambda rate: rate.GetCurrentTariffs()
    )
    """Function to get the current tariffs."""

    value_fn: Callable[
        [RateInfo, ValueInfoItem], StateType | date | datetime | Decimal
    ] = lambda _, tariff: tariff.value
    """Function to get the value of the sensor.
    Receives the rate info and the current tariff."""

    def unique_id_fn(self, rate_id: str) -> str:
        """Return a unique id for the entity."""
        return f"{rate_id}_{self.key}"


# Each of these sensors is created for every configured rate id
SENSOR_DESCRIPTIONS: tuple[MidasSensorEntityDescription, ...] = (
    MidasSensorEntityDescription(
        key="combined_energy_forecast",
        translation_key="combined_energy_forecast",
        icon="mdi:chart-line-variant",
        entity_registry_enabled_default=True,
    ),
    MidasSensorEntityDescription(
        key="current",
        translation_key="current",
        icon="mdi:meter-electric",
        native_unit_of_measurement="USD/kWh",
        suggested_display_precision=5,
    ),
    MidasSensorEntityDescription(
        key="current_tariff_name",
        translation_key="current_tariff_name",
        icon="mdi:text",
        entity_registry_enabled_default=False,
        value_fn=lambda _, tariff: tariff.ValueName,
    ),
    MidasSensorEntityDescription(
        key="current_tariff_start",
        translation_key="current_tariff_start",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda _, tariff: tariff.GetStart(),
    ),
    MidasSensorEntityDescription(
        key="current_tariff_end",
        translation_key="current_tariff_end",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        value_fn=lambda _, tariff: tariff.GetEnd(),
    ),
    MidasSensorEntityDescription(
        key="15min",
        translation_key="15min",
        icon="mdi:meter-electric",
        native_unit_of_measurement="USD/kWh",
        suggested_display_precision=5,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(minutes=15)  # noqa: DTZ005
        ),
    ),
    MidasSensorEntityDescription(
        key="15min_tariff_name",
        translation_key="15min_tariff_name",
        icon="mdi:text",
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(minutes=15)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.ValueName,
    ),
    MidasSensorEntityDescription(
        key="15min_tariff_start",
        translation_key="15min_tariff_start",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(minutes=15)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.GetStart(),
    ),
    MidasSensorEntityDescription(
        key="15min_tariff_end",
        translation_key="15min_tariff_end",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(minutes=15)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.GetEnd(),
    ),
    MidasSensorEntityDescription(
        key="1hour",
        translation_key="1hour",
        icon="mdi:meter-electric",
        native_unit_of_measurement="USD/kWh",
        suggested_display_precision=5,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(hours=1)  # noqa: DTZ005
        ),
    ),
    MidasSensorEntityDescription(
        key="1hour_tariff_name",
        translation_key="1hour_tariff_name",
        icon="mdi:text",
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(hours=1)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.ValueName,
    ),
    MidasSensorEntityDescription(
        key="1hour_tariff_start",
        translation_key="1hour_tariff_start",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(hours=1)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.GetStart(),
    ),
    MidasSensorEntityDescription(
        key="1hour_tariff_end",
        translation_key="1hour_tariff_end",
        icon="mdi:clock-end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        tariffs_fn=lambda rate: rate.GetActiveTariffs(
            datetime.now() + timedelta(hours=1)  # noqa: DTZ005
        ),
        value_fn=lambda _, tariff: tariff.GetEnd(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IntegrationMidasConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    entities = []
    
    # Create regular price sensors for each rate ID and description
    for description in SENSOR_DESCRIPTIONS:
        for rate_id in entry.runtime_data.rate_ids:
            if description.key != "combined_energy_forecast":
                entities.append(
                    MidasPriceSensor(
                        coordinator=entry.runtime_data.coordinator,
                        description=description,
                        rate_id=rate_id,
                    )
                )
    
    # Add the combined forecast sensor if we have multiple rate IDs
    if len(entry.runtime_data.rate_ids) > 0:
        combined_description = next(
            (d for d in SENSOR_DESCRIPTIONS if d.key == "combined_energy_forecast"), 
            None
        )
        if combined_description:
            entities.append(
                MidasCombinedForecastSensor(
                    coordinator=entry.runtime_data.coordinator,
                    description=combined_description,
                    rate_ids=entry.runtime_data.rate_ids,
                )
            )
    
    async_add_entities(entities)


class MidasPriceSensor(CoordinatorEntity[MidasDataUpdateCoordinator], SensorEntity):
    """MIDAS Price Sensor class."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    entity_description: MidasSensorEntityDescription

    def __init__(
        self,
        coordinator: MidasDataUpdateCoordinator,
        description: MidasSensorEntityDescription,
        rate_id: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator=coordinator)

        self.entity_description = description
        self._rate_id = rate_id
        self._attr_unique_id = description.unique_id_fn(self._rate_id)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._rate_id)},
            name=self._rate_id,
            manufacturer=None,
            model=None,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the native value of the sensor."""
        rate = self.coordinator.data[self._rate_id]
        tariffs = self.entity_description.tariffs_fn(rate)
        if len(tariffs) == 0:
            # No tariffs! Logging for this event is handled by the coordinator.
            return None
        tariff = tariffs[0]
        return self.entity_description.value_fn(rate, tariff)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Extra data for the sensor."""
        rate = self.coordinator.data[self._rate_id]
        tariffs = self.entity_description.tariffs_fn(rate)
        if len(tariffs) == 0:
            # No tariffs! Logging for this event is handled by the coordinator.
            return None
        tariff = tariffs[0]
        return {
            DATA_RATE_NAME: rate.RateName,
            DATA_RATE_TYPE: rate.RateType,
            DATA_RATE_URL: rate.RatePlan_Url,
            DATA_TARIFF_NAME: tariff.ValueName,
            DATA_START_TIME: tariff.GetStart(),
            DATA_END_TIME: tariff.GetEnd(),
        }

class MidasCombinedForecastSensor(CoordinatorEntity[MidasDataUpdateCoordinator], SensorEntity):
    """MIDAS Combined Energy Forecast Sensor for cheapest_energy_hours compatibility."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    entity_description: MidasSensorEntityDescription

    def __init__(
        self,
        coordinator: MidasDataUpdateCoordinator,
        description: MidasSensorEntityDescription,
        rate_ids: list[str],
    ) -> None:
        """Initialize the combined forecast sensor class."""
        super().__init__(coordinator=coordinator)

        self.entity_description = description
        self._rate_ids = rate_ids
        self._attr_unique_id = f"midas_combined_forecast"
        self._attr_name = "Combined Energy Price Forecast"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "combined_forecast")},
            name="MIDAS Combined Rate Forecast",
            manufacturer=None,
            model=None,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the native value of the sensor."""
        # Get current tariffs from all rates
        current_prices = []
        for rate_id in self._rate_ids:
            if rate_id not in self.coordinator.data:
                continue
            rate = self.coordinator.data[rate_id]
            tariffs = rate.GetCurrentTariffs()
            if tariffs:
                current_prices.append(tariffs[0].value)

        # Return the sum of current prices or None if no data
        if not current_prices:
            return None
        return sum(current_prices)

    def _create_combined_forecast(self, target_date: date) -> list[dict]:
        """Create a combined forecast for the specified date."""
        if not self._rate_ids or not self.coordinator.data:
            return []

        # Collect all intervals for the target date
        all_intervals = []
        for rate_id in self._rate_ids:
            if rate_id not in self.coordinator.data:
                continue

            rate = self.coordinator.data[rate_id]
            for tariff in rate.ValueInformation:
                start_time = tariff.GetStart()
                end_time = tariff.GetEnd()

                # Only include intervals that overlap with the target date
                start_date = start_time.date()
                end_date = end_time.date()

                if start_date <= target_date <= end_date:
                    # Adjust times to be within the target date
                    if start_date < target_date:
                        start_time = datetime.combine(target_date, datetime.min.time())
                    if end_date > target_date:
                        end_time = datetime.combine(target_date, datetime.max.time())

                    all_intervals.append({
                        "rate_id": rate_id,
                        "start": start_time,
                        "end": end_time,
                        "price": tariff.value
                    })

        if not all_intervals:
            return []

        # Sort intervals by start time
        all_intervals.sort(key=lambda x: x["start"])

        # Create a list of all unique interval boundaries
        boundaries = set()
        for interval in all_intervals:
            boundaries.add(interval["start"])
            boundaries.add(interval["end"])
        boundaries = sorted(list(boundaries))

        # Create combined intervals
        combined_intervals = []
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]

            # Find all tariffs active during this interval
            active_tariffs = {}  # Keyed by rate_id to avoid duplicates
            for interval in all_intervals:
                if interval["start"] <= start and interval["end"] >= end:
                    active_tariffs[interval["rate_id"]] = interval["price"]

            # Only create an interval if there are active tariffs
            if active_tariffs:
                combined_price = sum(active_tariffs.values())
                combined_intervals.append({
                    "start": start.isoformat(),
                    "price": combined_price
                })

        return combined_intervals

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return formatted attributes for cheapest_energy_hours compatibility."""
        if not self._rate_ids or not self.coordinator.data:
            return None

        # Get current time for filtering
        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # Generate combined forecasts for today and tomorrow
        raw_today = self._create_combined_forecast(today)
        raw_tomorrow = self._create_combined_forecast(tomorrow)

        # Filter out past intervals for today
        raw_today = [interval for interval in raw_today if parser.parse(interval["start"]) > now]

        # Basic rate info from the first rate
        first_rate_id = self._rate_ids[0] if self._rate_ids else None
        rate_info = {}
        if first_rate_id and first_rate_id in self.coordinator.data:
            rate = self.coordinator.data[first_rate_id]
            rate_info = {
                DATA_RATE_NAME: f"Combined Rates ({len(self._rate_ids)})",
                DATA_RATE_TYPE: rate.RateType,
                DATA_RATE_URL: rate.RatePlan_Url,
            }

        return {
            **rate_info,
            "raw_today": raw_today,
            "raw_tomorrow": raw_tomorrow,
            "tomorrow_valid": len(raw_tomorrow) > 0,
            "combined_rate_ids": self._rate_ids,
        }
