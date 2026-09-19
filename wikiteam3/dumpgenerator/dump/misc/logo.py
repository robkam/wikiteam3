import json
import os
import sys
from io import BytesIO

import requests
from PIL import Image

from wikiteam3.dumpgenerator.cli.delay import Delay
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.utils.identifier import url2prefix_from_config


def save_logo(config: Config, session: requests.Session):
    """Save the wiki logo as (prefix)-logo.extension"""
    print("Downloading logo")
    if not os.path.exists(f"{config.path}/siteinfo.json"):
        print("siteinfo.json not found, did the download fail? Cannot get logo URL")
        sys.exit(1)

    siteinfo = {}
    with open(f"{config.path}/siteinfo.json", "r", encoding="utf-8") as f:
        siteinfo = json.load(f)

    logo_url: str = siteinfo.get("query", {}).get("general", {}).get("logo", None)
    if not logo_url:
        print("No logo URL found in siteinfo.json, skipping logo download")
        return

    for tries_left in range(3, -1, -1):
        try:
            r = session.get(logo_url, stream=True, timeout=10)
            Delay(config=config)

            with Image.open(BytesIO(r.content)) as image:
                extension = next((ext for ext, fmt in Image.registered_extensions().items() if fmt == image.format), ".unknown")

                logo_filename = f"{config.path}/{url2prefix_from_config(config=config)}-{config.date}-logo{extension}"
                image.save(logo_filename)
                print(f"Saved logo as {logo_filename}")
                return

        except Exception as e:
            if tries_left == 0:
                print(f"Failed to download logo from {logo_url}: {e}")
                return

            print(f"Failed to download logo ({tries_left} tries left) from {logo_url}: {e}")