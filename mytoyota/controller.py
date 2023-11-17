"""Toyota Connected Services Controller """
# import annotations

from datetime import datetime, timedelta
from http import HTTPStatus
import logging
from typing import Any
import jwt  # For decoding taok
from urllib import parse  # For parse query string, can this be done with httpx?
import base64
import httpx

from mytoyota.const import (
    SUPPORTED_REGIONS,
    TIMEOUT,
    ACCESS_TOKEN_URL,
    AUTHENTICATE_URL,
    AUTHORIZE_URL,
)
from mytoyota.exceptions import (
    ToyotaActionNotSupported,
    ToyotaApiError,
    ToyotaInternalError,
    ToyotaLoginError,
)
from mytoyota.utils.logs import censor_dict

_LOGGER: logging.Logger = logging.getLogger(__package__)


class Controller:
    """Controller class."""
    BASIC_AUTH_STRING: str = base64.b64encode(b"oneapp:oneapp")

    def __init__(
            self,
            locale: str,
            region: str,
            username: str,
            password: str,
            brand: str,
            uuid: str | None = None,
    ) -> None:
        self._locale: str = locale
        self._region: str = region
        self._username: str = username
        self._password: str = password
        self._brand: str = brand
        self._uuid: str = uuid
        self._token: str | None = None
        self._token_expiration: datetime | None = None

    @property
    def _authorize_endpoint(self) -> str:
        """Returns auth endpoint."""
        return SUPPORTED_REGIONS[self._region].get(AUTHORIZE_URL)

    @property
    def _access_token_endpoint(self) -> str:
        """Returns auth endpoint."""
        return SUPPORTED_REGIONS[self._region].get(ACCESS_TOKEN_URL)

    @property
    def _authenticate_endpoint(self) -> str:
        """Returns auth endpoint."""
        return SUPPORTED_REGIONS[self._region].get(AUTHENTICATE_URL)

    #    @property
    #    def _auth_valid_endpoint(self) -> str:
    #        """Returns token is valid endpoint."""
    #        return SUPPORTED_REGIONS[self._region].get(TOKEN_VALID_URL)

    @property
    # TODO Dont think this is required outside of the controller anymore.
    def uuid(self) -> str | None:
        """Return uuid."""
        return self._uuid

    async def first_login(self) -> None:
        """Perform first login."""
        await self._update_token()

    async def _update_token(self, retry: bool = True) -> None:
        """Performs login to toyota servers and retrieves token and uuid for the account."""

        _LOGGER.debug("Authenticate")
        async with httpx.AsyncClient() as client:
            # Authenticate. (Better approach as found in toyota_na, as opposed to multiple stages)
            data = {}
            for _ in range(10):
                if "callbacks" in data:
                    for cb in data["callbacks"]:
                        if cb["type"] == "NameCallback" and cb["output"][0]["value"] == "User Name":
                            cb["input"][0]["value"] = self._username
                        elif cb["type"] == "PasswordCallback":
                            cb["input"][0]["value"] = self._password
                resp = await client.post(self._authenticate_endpoint, json=data)
                if resp.status_code != HTTPStatus.OK:
                    _LOGGER.error(f"Authenticcation failed:\n"
                                  f"  Status_Code = {resp.status_code}\n"
                                  f"  Text        = {resp.text}\n"
                                  f"  Headers     = {resp.headers}")
                    raise ToyotaLoginError("Could not authenticate")
                data = resp.json()
                if "tokenId" in data:
                    break

            if "tokenId" not in data:
                raise ToyotaLoginError("Authentication process looping")

            # Authorise
            resp = await client.get(self._authorize_endpoint,
                                    headers={"cookie": f"iPlanetDirectoryPro={data['tokenId']}"})
            if resp.status_code != HTTPStatus.FOUND:
                _LOGGER.error(f"Authorization failed:\n"
                              f"  Status_Code = {resp.status_code}\n"
                              f"  Text        = {resp.text}\n"
                              f"  Headers     = {resp.headers}")
                raise ToyotaLoginError("Authorization failed")
            authentication_code = parse.parse_qs(httpx.URL(resp.headers.get("location")).query.decode())["code"]

            # Retrieve tokens
            resp = await client.post(self._access_token_endpoint,
                                     headers={"authorization": "basic b25lYXBwOm9uZWFwcA=="},
                                     # f"basic {self.BASIC_AUTH_STRING}"},
                                     data={"client_id": "oneapp",
                                           "code": authentication_code,
                                           "redirect_uri": "com.toyota.oneapp:/oauth2Callback",
                                           "grant_type": "authorization_code",
                                           "code_verifier": "plain"})
            if resp.status_code != HTTPStatus.OK:
                _LOGGER.debug(f"Authorization failed:\n"
                              f"  Status_Code = {resp.status_code}\n"
                              f"  Text        = {resp.text}\n"
                              f"  Headers     = {resp.headers}")
                raise ToyotaLoginError("Failed to retrieve required tokens")

            access_tokens: dict[str, Any] = resp.json()
            assert ("access_token" in access_tokens and "id_token" in access_tokens)

            self._token = access_tokens["access_token"]
            self._uuid = jwt.decode(access_tokens["id_token"],
                                    algorithms=["RS256"],
                                    options={"verify_signature": False},
                                    audience="oneappsdkclient")["uuid"]  # Usefully found in toyota_na
            self._token_expiration = datetime.now() + timedelta(seconds=access_tokens["expires_in"])

    def _is_token_valid(self, retry: bool = True) -> bool:
        """Checks if token is valid"""
        if self._token == None:
            return False

        return self._token_expiration > datetime.now()

    async def request(  # pylint: disable=too-many-branches
            self,
            method: str,
            endpoint: str,
            base_url: str | None = None,
            body: dict[str, Any] | None = None,
            params: dict[str, Any] | None = None,
            headers: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """Shared request method"""
        if method not in ("GET", "POST", "PUT", "DELETE"):
            raise ToyotaInternalError("Invalid request method provided")

        if not self._is_token_valid():
            await self._update_token()

        if base_url:
            url = SUPPORTED_REGIONS[self._region].get(base_url) + endpoint
        else:
            url = endpoint

        _LOGGER.debug("Constructing additional headers...")
        if headers is None:
            headers = {}
        headers.update(
            {
                "x-api-key": "tTZipv6liF74PwMfk9Ed68AQ0bISswwf3iHQdqcF",
                "x-guid": self._uuid,
                "authorization": f"Bearer {self._token}",
                "x-channel": "ONEAPP",
                "x-brand": self._brand.upper()
            }
        )

        _LOGGER.debug(f"Additional headers: {censor_dict(headers.copy())}")

        # Cannot authenticate with aiohttp (returns 415),
        # but it works with httpx.
        _LOGGER.debug("Creating client...")
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            _LOGGER.debug(
                f"Body: {censor_dict(body) if body else body} - Parameters: {params}"
            )
            response = await client.request(
                method,
                url,
                headers=headers,
                json=body,
                params=params,
                follow_redirects=True,
            )
            if response.status_code in [
                HTTPStatus.OK,
                HTTPStatus.ACCEPTED,
            ]:
                ret: dict[str, Any] = response.json()
                if "payload" in ret:
                    return ret["payload"]

                return ret
            elif response.status_code == HTTPStatus.NO_CONTENT:
                # TODO
                raise ToyotaApiError("NO_CONTENT")
            elif response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
                # TODO
                raise ToyotaApiError("INTERNAL_SERVER_ERROR")
            elif response.status_code == HTTPStatus.BAD_GATEWAY:
                # TODO
                raise ToyotaApiError("Servers are overloaded, try again later")
            elif response.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
                # TODO
                raise ToyotaApiError("Servers are temporarily unavailable")
            elif response.status_code == HTTPStatus.FORBIDDEN:
                # TODO
                raise ToyotaActionNotSupported(
                    "Action is not supported on this vehicle"
                )
            else:
                raise ToyotaApiError(
                    f"HTTP: {response.status_code} - {response.text}"
                )

        return None  # Should not get here
