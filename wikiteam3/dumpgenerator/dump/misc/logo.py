import json
import os
import sys
from io import BytesIO

import requests
import filetype

from wikiteam3.dumpgenerator.cli.delay import Delay
from wikiteam3.dumpgenerator.config import Config
from wikiteam3.utils.identifier import url2prefix_from_config


def save_logo(config: Config, session: requests.Session):
    """Save the wiki logo as (prefix)-logo.{extension}"""
    print("Downloading logo")
    if not os.path.exists(f"{config.path}/siteinfo.json"):
        raise FileNotFoundError("siteinfo.json not found, did the download fail? Cannot get logo URL")

    siteinfo = {}
    with open(f"{config.path}/siteinfo.json", "r", encoding="utf-8") as f:
        siteinfo = json.load(f)

    logo_url: str|None = siteinfo.get("query", {}).get("general", {}).get("logo", None)
    if not logo_url:
        print("No logo URL found in siteinfo.json, skipping logo download")
        return

    for tries_left in range(3, -1, -1):
        Delay(config=config)
        try:
            r = session.get(logo_url, timeout=15)

            extension = filetype.guess_extension(r.content) or "unknown"
            extension = f".{extension}"

            _type = filetype.guess(r.content)
            is_image = _type is not None and any(m.mime == _type.mime for m in filetype.image_matchers)

            if not is_image:
                print(f"Downloaded file is not a valid image ({_type}), skipping logo save")
                return

            logo_filepath = f"{config.path}/{url2prefix_from_config(config=config)}-{config.date}-logo{extension}"
            with open(logo_filepath, "wb") as f:
                f.write(r.content)
            print(f"Saved logo as {logo_filepath}")
            return
        except Exception as e:
            if tries_left == 0:
                print(f"Failed to download logo from {logo_url}: {e}")
                return

            print(f"Failed to download logo ({tries_left} tries left) from {logo_url}: {e}")