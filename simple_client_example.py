"""Simple test of new API Changes."""
import asyncio
from datetime import date, timedelta
import json
import pprint

from mytoyota.client import MyT
from mytoyota.models.summary import SummaryType

pp = pprint.PrettyPrinter(indent=4)

# Set your username and password in a file on top level called "credentials.json" in the format:
#   {
#       "username": "<username>",
#       "password": "<password>"
#   }


def load_credentials():
    """Load credentials from 'credentials.json'."""
    try:
        with open("credentials.json", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return None


credentials = load_credentials()
if not credentials:
    raise ValueError(
        "Did you forget to set your username and password? Or supply the credentials file"
    )

USERNAME = credentials["username"]
PASSWORD = credentials["password"]

client = MyT(username=USERNAME, password=PASSWORD)


async def get_information():
    """Test login and output from endpoints."""
    print("Logging in...")
    await client.login()

    print("Retrieving cars...")
    cars = await client.get_vehicles(metric=False)

    for car in cars:
        await car.update()

        # Dashboard Information
        pp.pprint(f"Dashboard: {car.dashboard}")
        # Location Information
        pp.pprint(f"Location: {car.location}")
        # Lock Status
        pp.pprint(f"Lock Status: {car.lock_status}")
        # Notifications
        pp.pprint(f"Notifications: {[[x] for x in car.notifications]}")
        # Summary
        pp.pprint(
            f"Summary: {[[x] for x in await car.get_summary(date.today() - timedelta(days=6 * 30), date.today(), summary_type=SummaryType.MONTHLY)]}"  # noqa: E501 # pylint: disable=C0301
        )
        # Trips
        pp.pprint(
            f"Trips: f{await car.get_trips(date.today() - timedelta(days=2), date.today(), full_route=True)}"  # pylint: disable=C0301
        )

        # Dump all the information collected so far:
        # pp.pprint(car._dump_all())  # pylint: disable=W0212


loop = asyncio.get_event_loop()
loop.run_until_complete(get_information())
loop.close()
