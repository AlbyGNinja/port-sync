# port-sync
Small python script to sync forwarded port from gluetun container with the qbittorrent `listen_port` and `embedded_tracker_port` 

## Requirement
You have to edit your Gluetun container configuration adding new volume:

`/select/any/host/path:/tmp/gluetun`

In the Gluetun container folder `/tmp/gluetun` you can find the files `forwarded_port` and `ip` which contains, as the names say, the forwarded port chosen by the vpn provider, and the vpn IP.

## Configuration
Change the qBittorrent endpoint matching your own ip/domain and update credentials to use to login qBittorrent, this is required in order to update its settings.

PS: remember whenever you re-deploy Gluetun container you have to re assign it under network configuration mode as `container:<gluetun_service_id>` or if you use Portainer or similar, you have to re-select Gluetun container
