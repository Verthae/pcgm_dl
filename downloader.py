import os
import json
import time
import requests
# from multiprocessing import pool, cpu_count
from lib import ASSETS, BUNDLES, RAW


# Known valid versions / OS
versions = ["10001000", "10001100", "10001200", "10001300"]
OS = ["Android", "iOS"]

# Download Options
# MULTIPROCESS = True
HASH_PATH = True
usage = (versions[-1], OS[0])

BASE_URL = r"https://prd-priconne-grandmasters-hq6jkeih.akamaized.net"


def download(data):
    version, mobile_os = usage
    dl_data, dl_path = data
    dl_hash = dl_data['Hash']
    if HASH_PATH:
        target = dl_hash
        dl_path = os.path.join(dl_path, version, mobile_os, dl_hash[:2], dl_hash)
    else:
        target = dl_data["Name"]
        dl_path = os.path.join(dl_path, version, mobile_os, dl_data['Name'])
    os.makedirs(os.path.dirname(dl_path), exist_ok=True)
    response = requests.get(f"{BASE_URL}/{version}/Jpn/{mobile_os}/assetbundles/{dl_hash[:2]}/{dl_hash}")
    if response.status_code == 200:
        with open(dl_path, "wb") as dl_file:
            dl_file.write(response.content)
    else:
        raise FileNotFoundError
    if "dependency" in dl_data and len(dl_data['dependency']) > 0:
        with open(os.path.join(os.path.dirname(dl_path), f"{target}_dependency.txt"), "w") as dep_file:
            dep_file.write(dl_data["dependency"])
    # if not MULTIPROCESS:
    time.sleep(1)
    return dl_data['Name'], dl_hash


with open(r'assetbundle.manifest.json', 'r') as manifest:
    asset_list = json.loads(manifest.read())
    raw_hashes = []
    asset_downloaded = {}

    os.makedirs(ASSETS, exist_ok=True)
    asset_list_fp = os.path.join(ASSETS, "assetlist.txt")
    if os.path.exists(asset_list_fp):
        with open(asset_list_fp, "rt", encoding="utf8") as f:
            asset_downloaded = dict(line.strip().split("\t") for line in f if line.strip())
    asset_list_f = open(asset_list_fp, "ab", buffering=0)
    try:
        new_assets = []
        for asset in asset_list['asset']:
            if asset['Name'] not in asset_downloaded or asset_downloaded[asset['Name']] != asset['Hash']:
                new_assets.append((asset, BUNDLES))
        for asset in asset_list['raw_asset']:
            if asset['Name'] not in asset_downloaded or asset_downloaded[asset['Name']] != asset['Hash']:
                new_assets.append((asset, RAW))
        if new_assets:
            # if MULTIPROCESS:
            #     tpool = pool.Pool(cpu_count())
            #     itering = tpool.imap_unordered(download, new_assets)
            # else:
            itering = (download(x) for x in new_assets)

            for i, (name, ahash) in enumerate(itering):
                print(f"{i + 1}/{len(new_assets)} : {ahash} - {name}")
                asset_list_f.write(f"{name}\t{ahash}\n".encode("utf8"))
    except KeyboardInterrupt as e:
        pass
    asset_list_f.close()
