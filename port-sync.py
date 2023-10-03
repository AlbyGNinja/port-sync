#!/usr/bin/env python3

import enum
import logging
import sys
from typing import Final
import qbittorrentapi


@enum.unique
class ToolExitCodes(enum.IntEnum):
    ALL_GOOD = 0
    BASE_ERROR = 1
    QBIT_AUTH_FAILURE = 2
    HTTP_ERROR = 3
    INVALID_PORT = 4
    QBIT_PREF_MISSING = 5

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
