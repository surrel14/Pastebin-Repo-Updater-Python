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

def build_app_entry(extracted_info, existing=None):
    """
    Build a full app entry from extracted IPA info.
    If `existing` is provided, preserve fields that are not present in the IPA.
    """
    existing = existing or {}
    name = extracted_info.get("name") or existing.get("name", "")
    subtitle = extracted_info.get("displayName") or existing.get("subtitle", "") or existing.get("displayName", "")
    return {
        "beta": existing.get("beta", False),
        "name": name,
        "bundleIdentifier": extracted_info.get("bundleIdentifier", ""),
        "version": extracted_info.get("version", ""),
        "size": extracted_info.get("size", 0),
        "subtitle": subtitle,
        "developerName": existing.get("developerName", "UNKNOWN"),
        "versionDate": existing.get("versionDate", ""),
        "versionDescription": existing.get("versionDescription", ""),
        "downloadURL": existing.get("downloadURL", ""),
        "localizedDescription": existing.get("localizedDescription", ""),
        "iconURL": existing.get("iconURL", ""),
        "tintColor": existing.get("tintColor", "03befc"),
        "screenshotURLs": existing.get("screenshotURLs", []),
    }

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
        for idx, app in enumerate(db.get("apps", [])):
            if app.get("bundleIdentifier") == extracted_info.get("bundleIdentifier"):
                found = True
                print("✔ Overwriting existing JSON entry for:")
                print("   ", extracted_info["bundleIdentifier"])
                
                # Build a new entry, preserving other metadata from the existing record
                db["apps"][idx] = build_app_entry(extracted_info, existing=app)
        
        if not found:
            print("➕ Adding NEW app entry to JSON")
            db.setdefault("apps", []).append(build_app_entry(extracted_info, existing=None))

print("\n💾 Saving JSON...")
with open(JSON_FILE, 'w', encoding="utf-8") as f:
    json.dump(db, f, indent=2)

print("\n✅ Completed. JSON updated.")
