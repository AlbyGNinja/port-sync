#!/usr/bin/env python3

import enum
import logging
import sys
from typing import Dict
from typing import Final

import qbittorrentapi
import requests


@enum.unique
class ToolExitCodes(enum.IntEnum):
    ALL_GOOD = 0
    BASE_ERROR = 1
    QBIT_AUTH_FAILURE = 2
    HTTP_ERROR = 3
    INVALID_PORT = 4
    QBIT_PREF_MISSING = 5


class VpnServerException(BaseException):
    CODE = ToolExitCodes.BASE_ERROR


class VpnServerHttpCodeException(VpnServerException):
    CODE = ToolExitCodes.HTTP_ERROR


class VpnServerInvalidPortException(VpnServerException):
    CODE = ToolExitCodes.INVALID_PORT


class VpnControlServerApi(object):
    def __init__(self,
                 host: str,
                 port: int):
        self._log = logging.getLogger(__name__)
        self._host: Final[str] = host
        self._port: Final[int] = port

        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json"
        })

        self._API_BASE: Final[str] = f"http://{self._host}:{self._port}/v1"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()

    def _query(self, endpoint) -> Dict:
        uri = self._API_BASE + endpoint
        self._log.debug(f"Query to {uri}")
        r = self._session.get(uri)
        if r.status_code == 200:
            self._log.debug("API query completed")
            return r.json()
        else:
            self._log.error(f"API returned {r.status_code} for {endpoint} endpoint")
            raise VpnServerHttpCodeException()

    @property
    def forwarded_port(self) -> int:
        endpoint = "/openvpn/portforwarded"
        data = self._query(endpoint)
        if "port" in data:
            vpn_forwarded_port: int = int(data["port"])
            self._log.info(f"VPN Port is {vpn_forwarded_port}")
            if 1023 < vpn_forwarded_port < 65535:
                return vpn_forwarded_port
            else:
                self._log.info(f"VPN Port invalid: {vpn_forwarded_port}")
                raise VpnServerInvalidPortException()
        else:
            self._log.info("Missing port data")
            raise VpnServerInvalidPortException()


if __name__ == "__main__":

    # Torrent host and WebUI port
    _TORRENT_HOST: Final[str] = "localhost"
    _TORRENT_PORT: Final[int] = 8080    # default qBittorrent WebUI port

    __EXIT_CODE = ToolExitCodes.ALL_GOOD

    logging.basicConfig(level=logging.INFO,
                        datefmt="%Y-%m-%d %H:%M:%S",
                        format='%(asctime)s %(name)-10s %(levelname)-8s %(message)s')

    logger = logging.getLogger("port-tool")

    qbit_port: int = -1
    vpn_port: int = -1

    # forwarded_port file path chosen
    file_path = "/host/binded/folder/path/forwarded_port" # "forwarded_port" is the default name of Gluetun file where forwarded port information is saved

    # Try to read the file
    try:
        with open(file_path, 'r') as file:
            vpn_port = int(file.read().strip())
    except FileNotFoundError:
        print(f"File {file_path} non trovato.")
        exit(1)

    # Gather the qBittorent _port
    try:

        qbt_client = qbittorrentapi.Client(host=f'http://{_TORRENT_HOST}:{_TORRENT_PORT}',
                                           username='username',
                                           password='password')

        qbt_client.auth_log_in()

        logger.info(f'qBittorrent: {qbt_client.app.version}')
        logger.info(f'qBittorrent Web API: {qbt_client.app.web_api_version}')

        if "listen_port" in qbt_client.app.preferences:
            qbit_port: int = int(qbt_client.app.preferences["listen_port"])
            logger.info(f"Torrent Port is {qbit_port}")
        else:
            logger.error("Preference listen_port not found")
            __EXIT_CODE = ToolExitCodes.QBIT_PREF_MISSING

        # Change prefs if needed
        if __EXIT_CODE == ToolExitCodes.ALL_GOOD:
            if vpn_port != qbit_port:
                qbt_client.app.preferences = dict(listen_port=vpn_port)
                logger.info(f"Updated qBittorrent listening port to {vpn_port}")
                qbt_client.app.preferences = dict(embedded_tracker_port=vpn_port)
                logger.info(f"Updated qBittorrent tracker port to {vpn_port}")
            else:
                logger.info(f"Ports matched, no change ({vpn_port} == {qbit_port})")

    except qbittorrentapi.LoginFailed as e:
        logger.error(str(e))
        __EXIT_CODE = ToolExitCodes.QBIT_AUTH_FAILURE

    sys.exit(__EXIT_CODE)
