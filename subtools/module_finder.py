import requests


class ModuleFinder:
    def __init__(self):
        pass

    def _find_npm(self, lib_name: str):
        result_data = {}
        endpoint = f"https://registry.npmjs.org/{lib_name}"
        response = requests.get(endpoint)
        if response.status_code != 200:
            return None
        response_json = response.json()
        versions = response_json.get("versions")
        distribution_tags = response_json.get("dist-tags")
        for key, value in distribution_tags.items():
            version_requested = versions.get(value, {})
            result_data[key] = version_requested
        return {
            "versions_latest": distribution_tags,
            "version_latest_data": result_data,
        }

    def _find_pypi(self, lib_name: str):
        final_output = {"releases_info": []}
        endpoint = f"https://pypi.org/pypi/{lib_name}/json"
        response = requests.get(endpoint)
        if response.status_code != 200:
            return None
        result_json = response.json()
        information_data = result_json.get("info")
        releases = result_json.get("releases", {})
        latest_5_releases = list(releases.keys())[-5:]
        for release_loop in latest_5_releases:
            final_output["releases_info"].append(
                {"version": release_loop, "data": releases[release_loop]}
            )
        final_output["info"] = information_data
        return final_output

    def _find_maven(self, group_id: str, artifact_id: str):
        """
        Maven Central Search API.
        """
        endpoint = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&rows=5&wt=json"
        response = requests.get(endpoint)
        if response.status_code != 200:
            return None
        docs = response.json().get("response", {}).get("docs", [])
        return docs if docs else None

    def _find_packagist(self, lib_name: str):
        """
        Packagist (PHP Composer) registry
        """
        endpoint = f"https://repo.packagist.org/p/{lib_name}.json"
        response = requests.get(endpoint)
        if response.status_code != 200:
            return None
        response_json = response.json()
        return response_json.get("packages", {}).get(lib_name, {})

    def _find_rubygems(self, lib_name: str):
        """
        RubyGems registry
        """
        endpoint = f"https://rubygems.org/api/v1/gems/{lib_name}.json"
        response = requests.get(endpoint)
        if response.status_code != 200:
            return None
        return response.json()

    def _get_cve_data(self, cve_id: str):
        base_url = f"https://cve.circl.lu/api/cve/{cve_id}"
        response = requests.get(base_url)
        if response.status_code != 200:
            return None
        return response.json()

    def add_tools(self, mcp_server):
        @mcp_server.tool()
        async def get_cve_data(cve_id: str):
            """
            Fetch CVE data from the NVD API.

            Args:
                cve_id (str): The CVE identifier (e.g., "CVE-2021-12345").

            Returns:
                dict: CVE data if found, otherwise None.
                This will search from services.nvd.nists.gov.
            """
            return self._get_cve_data(cve_id)

        @mcp_server.tool()
        async def find_module(
            lib_name: str,
            package_manager: str = "npm",
            group_id: str = None,
            artifact_id: str = None,
        ) -> dict:
            """
            Find a module in the specified package manager.

            Args:
                lib_name (str): The name of the library to find (npm, pypi, packagist, rubygems).
                package_manager (str): The package manager ("npm", "pypi", "maven", "packagist", "rubygems").
                group_id (str): Maven group ID (required if package_manager == "maven").
                artifact_id (str): Maven artifact ID (required if package_manager == "maven").

            Returns:
                dict: Information about the library if found, otherwise None.
            """
            if package_manager == "npm":
                return self._find_npm(lib_name)
            elif package_manager == "pypi":
                return self._find_pypi(lib_name)
            elif package_manager == "maven":
                if not group_id or not artifact_id:
                    raise ValueError("Maven requires group_id and artifact_id.")
                return self._find_maven(group_id, artifact_id)
            elif package_manager == "packagist":
                return self._find_packagist(lib_name)
            elif package_manager == "rubygems":
                return self._find_rubygems(lib_name)
            else:
                raise ValueError(
                    "Unsupported package manager. Use 'npm', 'pypi', 'maven', 'packagist', or 'rubygems'."
                )

        # Return both functions as a tuple or dict
        return {"find_module": find_module, "get_cve_data": get_cve_data}