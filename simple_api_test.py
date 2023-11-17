import asyncio
import pprint
from mytoyota.client import Api, Controller

pp = pprint.PrettyPrinter()


async def main():
        control = Controller("en-gb", "europe", "car@rebeccaodonnell.co.uk", "10Bumhead!", "T")
        api = Api(control)
        await api.controller.first_login()

        print("----- get_vehicles_endpoint -----\n")
        vehicles = await api.get_vehicles_endpoint()
        pp.pprint(vehicles)
        print("----- get_parking_endpoint -----\n")
        parking = await api.get_parking_endpoint(vehicles[0]["vin"])
        pp.pprint(parking)
        print("----- get_vehicle_status_endpoint -----\n")
        status = await api.get_vehicle_status_endpoint(vehicles[0]["vin"])
        pp.pprint(status)
        print("----- get_vehicle_electric_status_endpoint -----\n")
        electric_status = await api.get_vehicle_electric_status_endpoint(vehicles[0]["vin"])
        pp.pprint(electric_status)
        print("----- get_telemetry_endpoint -----\n")
        telemetry = await api.get_telemetry_endpoint(vehicles[0]["vin"])
        pp.pprint(telemetry)






asyncio.run(main())
