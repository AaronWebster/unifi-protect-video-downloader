import json
import tempfile

import click

from protect_archiver.cli.base import cli
from protect_archiver.client import ProtectClient
from protect_archiver.config import Config
from protect_archiver.errors import ProtectError


@cli.command("list", help="List available footage ranges for each camera in JSON format")
@click.option(
    "--address",
    default=Config.ADDRESS,
    show_default=True,
    required=True,
    help="IP address or hostname of the UniFi Protect Server",
    envvar="PROTECT_ADDRESS",
    show_envvar=True,
)
@click.option(
    "--port",
    default=Config.PORT,
    show_default=True,
    required=False,
    help="The port of the UniFi Protect Server",
    envvar="PROTECT_PORT",
    show_envvar=True,
)
@click.option(
    "--not-unifi-os",
    is_flag=True,
    default=False,
    show_default=True,
    help="Use this for systems without UniFi OS",
    envvar="PROTECT_NOT_UNIFI_OS",
    show_envvar=True,
)
@click.option(
    "--username",
    required=True,
    help="Username of user with local access",
    prompt="Username of local Protect user",
    envvar="PROTECT_USERNAME",
    show_envvar=True,
)
@click.option(
    "--password",
    required=True,
    help="Password of user with local access",
    prompt="Password for local Protect user",
    hide_input=True,
    envvar="PROTECT_PASSWORD",
    show_envvar=True,
)
@click.option(
    "--verify-ssl",
    is_flag=True,
    default=False,
    show_default=True,
    help="Verify Protect SSL certificate",
    envvar="PROTECT_VERIFY_SSL",
    show_envvar=True,
)
@click.option(
    "--cameras",
    default="all",
    show_default=True,
    help=(
        "Comma-separated list of one or more camera IDs ('--cameras=\"id_1,id_2,id_3,...\"'). "
        "Use '--cameras=all' to list footage ranges for all available cameras."
    ),
    envvar="PROTECT_CAMERAS",
    show_envvar=True,
)
def list_footage(
    address: str,
    port: int,
    not_unifi_os: bool,
    username: str,
    password: str,
    verify_ssl: bool,
    cameras: str,
) -> None:
    client = ProtectClient(
        address=address,
        port=port,
        not_unifi_os=not_unifi_os,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
        destination_path=tempfile.gettempdir(),  # Not used for listing, but required by ProtectClient
    )

    try:
        from datetime import datetime

        # get camera list
        camera_list = client.get_camera_list()

        if cameras != "all":
            camera_s = set(cameras.split(","))
            camera_list = [c for c in camera_list if c.id in camera_s]

        # Build output data structure
        footage_ranges = {}
        for camera in sorted(camera_list, key=lambda c: c.name):
            # Convert datetime objects to ISO format strings for JSON serialization
            start_str = (
                camera.recording_start.isoformat()
                if camera.recording_start != datetime.min
                else None
            )
            end_str = (
                camera.recording_end.isoformat() if camera.recording_end != datetime.min else None
            )

            # Create sorted interval set (single interval per camera)
            intervals = []
            if start_str and end_str:
                intervals.append({"start": start_str, "end": end_str})

            footage_ranges[camera.id] = {
                "name": camera.name,
                "intervals": intervals,
            }

        # Output as JSON
        print(json.dumps(footage_ranges, indent=2, sort_keys=True))

    except ProtectError as e:
        exit(e.code)
