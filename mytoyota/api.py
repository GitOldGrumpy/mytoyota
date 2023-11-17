"""Toyota Connected Services API"""
from typing import Any

from .const import BASE_URL
from .controller import Controller
from .exceptions import ToyotaApiError


class Api:
    """Controller class."""

    def __init__(self, controller: Controller) -> None:
        """Toyota Controller"""
        self.controller = controller

    @property
    def uuid(self) -> str | None:
        """Returns uuid from controller"""
        return self.controller.uuid

    async def set_vehicle_alias_endpoint(
        self, new_alias: str, vehicle_id: int
    ) -> dict[str, Any] | None:
        # It does seem to support it. Need to find the endpoint.
        raise NotImplemented("Endpoint not found")

    async def get_vehicles_endpoint(self) -> list[dict[str, Any] | None] | None:
        """Retrieves list of cars you have registered with MyT"""
        return await self.controller.request(
            method="GET",
            base_url=BASE_URL,
            endpoint="/v2/vehicle/guid",
        )

    async def get_connected_services_endpoint(self, vin: str) -> dict[str, Any] | None:
        """Get information about connected services for the given car."""
        raise NotImplemented("Endpoint no longer supported")

    async def get_odometer_endpoint(self, vin: str) -> list[dict[str, Any]] | None:
        """Get information from odometer."""
        raise NotImplemented("Endpoint no longer supported")

    async def get_location_endpoint(
        self, vin: str
    ) -> dict[str, Any] | None:  # pragma: no cover
        """Get where you have parked your car."""
        ret = await self.controller.request(
            method="GET",
            base_url=BASE_URL,
            endpoint=f"/v1/location",
            headers={"VIN": vin}
        )

        # If car is in motion you can get an empty response back. This will have no payload.
        if "status" in ret:
            return None

        return ret

    async def get_vehicle_status_endpoint(self, vin: str) -> dict[str, Any] | None:
        """Get information about the vehicle."""
        return await self.controller.request(
            method="GET",
            base_url=BASE_URL,
            endpoint="/v1/vehiclehealth/status",
            headers={"VIN": vin}
        )

    async def get_vehicle_electric_status_endpoint(self, vin: str) -> dict[str, Any] | None:
        """Get information about the vehicle."""
        try:
            return await self.controller.request(
                method="GET",
                base_url=BASE_URL,
                endpoint="/v1/global/remote/electric/status",
                headers={"VIN": vin}
            )
        except ToyotaApiError as e:
            # TODO This is wrong, but lets change the Vehicle class
            return None


    async def get_telemetry_endpoint(self, vin: str) -> dict[str, Any] | None:
        """Get information about the vehicle."""
        return await self.controller.request(
            method="GET",
            base_url=BASE_URL,
            endpoint="/v3/telemetry",
            headers={"VIN": vin}
        )

    async def get_vehicle_status_legacy_endpoint(
        self, vin: str
    ) -> dict[str, Any] | None:
        """Get information about the vehicle."""
        raise NotImplemented("Endpoint no longer supported")

    async def get_driving_statistics_endpoint(
        self, vin: str, from_date: str, interval: str | None = None
    ) -> dict[str, Any] | None:
        """Get driving statistic"""
        return await self.controller.request(
            method="GET",
            base_url=BASE_URL,
            endpoint="/v2/trips/summarize",
            headers={"vin": vin},
            params={"from": from_date, "calendarInterval": interval},
        )

    async def get_trips_endpoint(
        self,
        vin: str,
        page: int = 1,
    ) -> dict[str, Any] | None:
        """Get trip
        The page parameter works a bit strange but setting to 1 gets last few trips"""
        return await self.controller.request(
            method="GET",
            base_url=BASE_URL_CARS,
            endpoint=f"/api/user/{self.uuid}/cms/trips/v2/history/vin/{vin}/{page}",
            headers={"vin": vin},
        )

    async def get_trip_endpoint(self, vin: str, trip_id: str) -> dict[str, Any] | None:
        """Get data for a single trip"""
        return await self.controller.request(
            method="GET",
            base_url=BASE_URL_CARS,
            endpoint=f"/api/user/{self.uuid}/cms/trips/v2/{trip_id}/events/vin/{vin}",
            headers={"vin": vin},
        )

    async def set_lock_unlock_vehicle_endpoint(
        self, vin: str, action: str
    ) -> dict[str, str] | None:
        """Lock vehicle."""
        return await self.controller.request(
            method="POST",
            base_url=BASE_URL,
            endpoint=f"/vehicles/{vin}/lock",
            body={"action": action},
        )

    async def get_lock_unlock_request_status(
        self, vin: str, request_id: str
    ) -> dict[str, Any] | None:
        """Check lock/unlock status given a request ID"""
        return await self.controller.request(
            method="GET",
            base_url=BASE_URL,
            endpoint=f"/vehicles/{vin}/lock/{request_id}",
        )
