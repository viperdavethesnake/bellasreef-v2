import requests

BASE_URL = "http://192.168.33.122:8001"
AUTH_HEADER = {"Authorization": "Bearer ab7941c9e0957d7d3394da288f3c5e08af6ff7d7cde2188b44b37ec808bbde16"}


def test_probe_workflow():
    print("Testing Temp Probe API workflow...\n")

    # List probes
    r = requests.get(f"{BASE_URL}/probe/list", headers=AUTH_HEADER)
    assert r.status_code == 200
    probes = r.json()
    assert isinstance(probes, list)
    print("✅ List probes passed")

    # Discover hardware
    r = requests.get(f"{BASE_URL}/probe/discover", headers=AUTH_HEADER)
    assert r.status_code == 200
    hardware = r.json()
    assert isinstance(hardware, list)
    print("✅ Discover hardware passed")

    # Add first probe
    probe1 = {
        "hardware_id": "000000bd39d7",
        "name": "Cabinet Temp Probe",
        "type": "temperature",
        "unit": "C",
        "polling_interval": 10,
        "enabled": True
    }
    r = requests.post(f"{BASE_URL}/probe/", headers={**AUTH_HEADER, "Content-Type": "application/json"}, json=probe1)
    assert r.status_code == 200
    data = r.json()
    assert data["hardware_id"] == probe1["hardware_id"]
    print("✅ Add first probe passed")

    # Get current temp of first probe
    r = requests.get(f"{BASE_URL}/probe/{probe1['hardware_id']}/temperature", headers=AUTH_HEADER)
    assert r.status_code == 200
    temp_data = r.json()
    assert temp_data["hardware_id"] == probe1["hardware_id"]
    assert isinstance(temp_data["temperature"], float)
    assert temp_data["unit"] == "C"
    print("✅ Get current temp of first probe passed")

    # Add second probe
    probe2 = {
        "hardware_id": "000000be52f2",
        "name": "Sump Temp Probe",
        "type": "temperature",
        "unit": "C",
        "polling_interval": 10,
        "enabled": True
    }
    r = requests.post(f"{BASE_URL}/probe/", headers={**AUTH_HEADER, "Content-Type": "application/json"}, json=probe2)
    assert r.status_code in (200, 400)  # 400 if already exists
    if r.status_code == 200:
        data = r.json()
        assert data["hardware_id"] == probe2["hardware_id"]
        print("✅ Add second probe passed")
    else:
        assert r.json()["detail"] == "Probe with this hardware ID already exists."
        print("⚠️  Add second probe skipped (already exists)")

    # List probes
    r = requests.get(f"{BASE_URL}/probe/list", headers=AUTH_HEADER)
    assert r.status_code == 200
    probes = r.json()
    assert any(p["hardware_id"] == probe1["hardware_id"] for p in probes)
    assert any(p["hardware_id"] == probe2["hardware_id"] for p in probes)
    print("✅ List probes (after adds) passed")

    # Delete first probe
    r = requests.delete(f"{BASE_URL}/probe/{probe1['hardware_id']}", headers=AUTH_HEADER)
    assert r.status_code == 204
    print("✅ Delete first probe passed")

    # List probes
    r = requests.get(f"{BASE_URL}/probe/list", headers=AUTH_HEADER)
    assert r.status_code == 200
    probes = r.json()
    assert all(p["hardware_id"] != probe1["hardware_id"] for p in probes)
    assert any(p["hardware_id"] == probe2["hardware_id"] for p in probes)
    print("✅ List probes (after delete) passed")

    print("\n🎉 All Temp Probe API tests completed successfully!")


if __name__ == "__main__":
    test_probe_workflow()
