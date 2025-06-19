import requests

def get_sdrangel_status(ip_address):
    url = f"http://{ip_address}:8091"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()  # Return the JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error accessing SDRangel: {e}")
        return None

if __name__ == "__main__":
    ip_address = "204.84.22.107"
    status = get_sdrangel_status(ip_address)
    if status:
        print("SDRangel Status:", status)
