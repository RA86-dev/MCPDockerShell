import requests
def _find_cve(
    cve: str
):
    base_url =f"https://cve.circl.lu/api/cve/{cve}"
    d = requests.get(base_url)
    return d.json()
    

if __name__ == "__main__":
    print(_find_cve("CVE-2025-9604"))