"""Vehicle model."""
from __future__ import annotations

import logging
from typing import Any

from mytoyota.models.dashboard import Dashboard
from mytoyota.models.hvac import Hvac
from mytoyota.models.location import ParkingLocation
from mytoyota.models.sensors import Sensors
from mytoyota.utils.formatters import format_odometer
from mytoyota.utils.logs import censor_vin

_LOGGER: logging.Logger = logging.getLogger(__package__)


class Vehicle:
    """Vehicle data representation."""

    def __init__(
        self,
        vehicle_info: dict[str, Any],
        status: dict[str, Any] | None = None,
        electric_status: dict[str, Any] | None = None,
        telemetry: dict[str, Any] | None = None,
        location: dict[str, Any] | None = None,
    ) -> None:
        self._vehicle_info = vehicle_info
        self._status = status
        self._electric_status = electric_status
        self._telemetry = telemetry
        self._location = location


    @property
    def vehicle_id(self) -> int | None:
        """Vehicle's id."""
        #  "id" no longer exists => try imei
        return self._vehicle_info.get("imei")

    @property
    def vin(self) -> str | None:
        """Vehicle's vinnumber."""
        return self._vehicle_info.get("vin")

    @property
    def alias(self) -> str | None:
        """Vehicle's alias."""
        return self._vehicle_info.get("alias", "My vehicle")

    @property
    def hybrid(self) -> bool:
        """If the vehicle is a hybrid."""
        # "hybrid" no longer exists. "Check evVehicle". Could possibly then further check electric status.
        # Then change this to type if we have both Electric & Hybrid options
        return self._vehicle_info.get("evVehicle", False)

    @property
    def fueltype(self) -> str:
        """Fuel type of the vehicle."""
        fuelType = self._vehicle_info.get("fuelType", "Unknown")
        if fuelType != "Unknown":
            # Need to now further types. Only seen "I" or petrol cars.
            fuel_types = {"I": "Petrol"}
            if fuelType in fuel_types:
                return fuel_types["fuelType"]
            else:
                logging.warning(f"Unknown fuel type: {fuelType}")

        return "Unknown"

    @property
    def details(self) -> dict[str, Any] | None:
        """Formats vehicle info into a dict."""
        det: dict[str, Any] = {}
        for i in sorted(self._vehicle_info):
            if i in ("vin", "alias", "imei", "evVehicle"):
                continue
            det[i] = self._vehicle_info[i]
        return det if det else None

    @property
    def is_connected_services_enabled(self) -> bool:
        """Checks if the user has enabled connected services."""
        # Currently return true until we have connected to check what is and isn't available
        return True

    @property
    def parkinglocation(self) -> ParkingLocation | None:
        """Last parking location."""
        if self._location and 'vehicleLocation' in self._location:
            return ParkingLocation(self._location["vehicleLocation"])
        return None

    @property
    def sensors(self) -> Sensors | None:
        """Vehicle sensors."""
        # None of my cars have "protectionState" what was this supposed to return?
        return None

    @property
    def hvac(self) -> Hvac | None:
        """Vehicle hvac."""
        # This info is available need to find the endpoint.
        return None

    @property
    def dashboard(self) -> Dashboard | None:
        """Vehicle dashboard."""
        if self.is_connected_services_enabled and self.odometer:
            return Dashboard(self)
        return None
