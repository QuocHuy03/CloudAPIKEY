import requests
import random
from config import SUDO_KEYS_FILE, EXPIRED_SUDO_KEYS_FILE


def load_sudo_keys():
    try:
        with open(SUDO_KEYS_FILE, "r") as file:
            return file.read().splitlines()
    except Exception as e:
        print(f"Error loading API keys: {e}")
        return []


def update_sudo_keys(api_key_to_remove):
    try:
        with open(SUDO_KEYS_FILE, "r") as file:
            keys = file.readlines()

        # Remove the expired API key from the list
        with open(SUDO_KEYS_FILE, "w") as file:
            for key in keys:
                if api_key_to_remove.strip() != key.strip():
                    file.write(key)

        print(f"Removed expired key: {api_key_to_remove}")

        # Add the expired key to the expired keys file
        with open(EXPIRED_SUDO_KEYS_FILE, "a") as expired_file:
            expired_file.write(f"{api_key_to_remove}\n")

    except Exception as e:
        print(f"Error updating keys: {e}")


def generate_music(prompt_text, title, style, instrumental, api_key_list, proxies=None):
    if proxies is None or not proxies:
        proxies = [None]

    print(f"Proxies: {proxies}")

    def task(api_key, proxy_dict):
        try:
            url = "https://api.sunoapi.org/api/v1/generate"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            data = {
                "prompt": prompt_text,
                "title": title,
                "style": style,
                "customMode": True,
                "Instrumental": instrumental,
                "model": "V4",
                "negativeTags": "Heavy Metal, Upbeat Drums",
                "callBackUrl": "https://api.example.com/callback"
            }

            print(f"Calling API with key: {api_key[:20]}..., proxy: {proxy_dict}")

            response = requests.post(url, headers=headers, json=data, proxies=proxy_dict, timeout=60)

            if response.status_code != 200:
                raise Exception(f"HTTP Error {response.status_code}: {response.text[:300]}")

            # Get the response as JSON
            res_json = response.json()

            if res_json.get("code") == 429:
                print(f"Key {api_key[:20]} failed due to insufficient credits. Moving to expired keys.")
                update_sudo_keys(api_key)
                return {"success": False, "message": "Insufficient credits."}

            task_id = res_json.get("data", {}).get("taskId", None)

            if not task_id:
                raise Exception("No taskId found in the response.")

            print(f"Task started successfully. Task ID: {task_id}")
            return {"success": True, "data": {"taskId": task_id}, "api_key": api_key}

        except Exception as e:
            print(f"Key {api_key[:20]} error: {e}")
            if response and response.status_code == 429:
                print(f"Key {api_key[:20]} failed due to insufficient credits. Moving to expired keys.")
                update_sudo_keys(api_key)
            return {"success": False, "message": f"Error: {str(e)}"}

    # Distribute proxy across API keys
    for i, api_key in enumerate(api_key_list):
        proxy_str = proxies[i % len(proxies)]
        proxy_dict = {"http": proxy_str, "https": proxy_str} if proxy_str else None
        print(f"[MUSIC] Trying key {i+1}/{len(api_key_list)}: {api_key[:20]} with proxy: {proxy_str}")

        # Call task function and retry with the next API key if this one fails
        result = task(api_key, proxy_dict)
        if result.get("success"):
            return result  # Return task_id and the corresponding API key
        else:
            print(f"Key {api_key[:20]} unavailable. Trying next key.")

    return {"success": False, "message": "No valid key available for music generation."}


def check_task_status(task_id, api_key, proxies=None):
    status_url = "https://api.sunoapi.org/api/v1/generate/record-info"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        # If multiple proxies are provided, choose one randomly
        selected_proxy = None
        if proxies:
            if isinstance(proxies, list) and all(isinstance(proxy, dict) for proxy in proxies):
                selected_proxy = random.choice(proxies)
                print(f"Using proxy: {selected_proxy}")
            else:
                raise ValueError("Proxies should be a list of dictionaries with 'http' and 'https' keys.")

        # Send request to check task status
        params = {"taskId": task_id}
        response = requests.get(status_url, headers=headers, params=params, proxies=selected_proxy, timeout=30)

        # Handle HTTP response
        if response.status_code == 200:
            status_data = response.json()
            print(status_data)
            # Check if the response contains 'data'
            if "data" in status_data:
                return {"success": True, "data": status_data["data"]}
            
            return {"success": False, "message": "Data not found in the response."}

        elif response.status_code == 429:
            error_data = response.json()
            if error_data.get("msg") == "The current credits are insufficient. Please top up.":
                print("Error: Insufficient credits. Please top up your account.")
                return {"success": False, "message": "Insufficient credits."}
            else:
                raise Exception(f"Error: {error_data.get('msg', 'Unknown error')}")

        else:
            raise Exception(f"Error during status check: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error occurred: {str(e)}")
        return {"success": False, "message": f"Network error: {str(e)}"}
    except ValueError as e:
        print(f"❌ Value error occurred: {str(e)}")
        return {"success": False, "message": f"Value error: {str(e)}"}
    except Exception as e:
        print(f"❌ An unexpected error occurred: {str(e)}")
        return {"success": False, "message": f"Unexpected error: {str(e)}"}
