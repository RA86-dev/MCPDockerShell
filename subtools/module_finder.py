import requests
class ModuleFinder:
    def __init__(self):
        pass

    def _find_npm(self,lib_name: str):
        result_data = {}
        endpoint = f"https://registry.npmjs.org/{lib_name}"
        response = requests.get(endpoint)
        if response.status_code != 200:
            return None
        response_json = response.json()
        versions = response_json.get("versions")
        distribution_tags = response_json.get("dist-tags")
        for key, value in distribution_tags.items():
            version_requested = versions[value]
            result_data[key] = version_requested
        return {
            "versions_latest":distribution_tags,
            "version_latest_data":result_data
        }
    def _find_pypi(self,lib_name: str):
        final_output = {
            "releases_info":[]
        }
        endpoint = f"https://pypi.org/pypi/{lib_name}/json"
        response = requests.get(endpoint)
        if response.status_code != 200:
            return None
        result_json = response.json()
        information_data = result_json.get('info')
        releases = result_json.get("releases")
        latest_5_releases = releases.key()[5:]

        for release_loop in latest_5_releases:
            final_output['releases_info'].append(
                {
                    "version":release_loop,
                    "data": releases[release_loop]
                }
            )
        final_output['info'] = information_data
        return final_output

    def add_tools(self, mcp_server):
        @mcp_server.tool()
        async def find_module(
            lib_name: str, package_manager: str = "npm"
        ) -> dict:
            """
            Find a module in the specified package manager.

            Args:
                lib_name (str): The name of the library to find.
                package_manager (str): The package manager to use ("npm" or "pypi").
                If not specified, defaults to "npm".

            Returns:
                dict: Information about the library if found, otherwise None.
            """
            if package_manager == "npm":
                return self._find_npm(lib_name)
            elif package_manager == "pypi":
                return self._find_pypi(lib_name)
            else:
                raise ValueError("Unsupported package manager. Use 'npm' or 'pypi'."
        )
