import zipfile
import plistlib
import json
import os

JSON_FILE = "repo.json"
IPA_FOLDER = "ipas"

def get_ipa_info(ipa_path):
    info = {}
    with zipfile.ZipFile(ipa_path, 'r') as zip_ref:
        plist_file = None
        for name in zip_ref.namelist():
            if name.endswith("Info.plist") and name.startswith("Payload/"):
                plist_file = name
                break

        if not plist_file:
            return None
        
        with zip_ref.open(plist_file) as f:
            plist_data = plistlib.load(f)
            info["bundleIdentifier"] = plist_data.get("CFBundleIdentifier", "")
            info["version"] = plist_data.get("CFBundleShortVersionString", "")
            info["name"] = plist_data.get("CFBundleName", "")
            info["displayName"] = plist_data.get("CFBundleDisplayName", "")

    info["size"] = os.path.getsize(ipa_path)
    return info

print("Loading JSON...")
with open(JSON_FILE, 'r', encoding="utf-8") as f:
    db = json.load(f)

for file in os.listdir(IPA_FOLDER):
    if file.endswith(".ipa"):
        ipa_path = os.path.join(IPA_FOLDER, file)
        print(f"\n📦 Processing {file}")
        
        extracted_info = get_ipa_info(ipa_path)
        if not extracted_info:
            print("⚠️ Info.plist not found in IPA")
            continue
        
        found = False
        for app in db["apps"]:
            if app["bundleIdentifier"] == extracted_info["bundleIdentifier"]:
                found = True
                print("✔ Updating existing JSON entry:")
                print("   ", extracted_info["bundleIdentifier"])
                
                app["version"] = extracted_info["version"]
                app["size"] = extracted_info["size"]

                if extracted_info["name"]:
                    app["name"] = extracted_info["name"]

                if extracted_info["displayName"]:
                    app["subtitle"] = extracted_info["displayName"]
        
        if not found:
            print("➕ Adding NEW app entry to JSON")
            db["apps"].append({
                "beta": False,
                "name": extracted_info["name"],
                "bundleIdentifier": extracted_info["bundleIdentifier"],
                "version": extracted_info["version"],
                "size": extracted_info["size"],
                "subtitle": extracted_info["displayName"],
                "developerName": "UNKNOWN",
                "versionDate": "",
                "versionDescription": "",
                "downloadURL": "",
                "localizedDescription": "",
                "iconURL": "",
                "tintColor": "03befc",
                "screenshotURLs": []
            })

print("\n💾 Saving JSON...")
with open(JSON_FILE, 'w', encoding="utf-8") as f:
    json.dump(db, f, indent=2)

print("\n✅ Completed. JSON updated.")
