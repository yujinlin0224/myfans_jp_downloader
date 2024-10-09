from typing import cast

import user_agents

from config import Config

chromium_browsers_dict = {
    "chrome": "Google Chrome",
    "edge": "Microsoft Edge",
    "opera": "Opera",
}


def get_headers(config: Config) -> dict[str, str | bytes]:
    user_agent = user_agents.parse(config.request.user_agent)

    browser = cast(user_agents.parsers.Browser, user_agent.browser)
    browser_family = cast(str, browser.family)

    def get_sec_ch_ua_dict() -> dict[str, str]:
        if browser_family.lower() not in chromium_browsers_dict:
            return {}

        browser_version = cast(tuple[int], browser.version)[0]
        os = cast(user_agents.parsers.OperatingSystem, user_agent.os)
        os_family = cast(str, os.family)
        if os_family.lower() == "mac os x":
            os_family = "macOS"

        greasey_brand = '"Not=A?Brand";v="8"'
        chromium_brand = f'"Chromium";v="{browser_version}"'
        browser_brand = (
            f'"{chromium_browsers_dict[browser_family]}";v="{browser_version}"'
        )

        return {
            "Sec-CH-UA": f"{greasey_brand}, {chromium_brand}, {browser_brand}",
            "Sec-CH-UA-Mobile": "?1" if user_agent.is_mobile else "?0",
            "Sec-CH-UA-Platform": os_family,
        }

    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ja-JP,ja;q=0.9",
        "Authorization": f"Token token={config.auth.token}",
        "Cache-Control": "no-cache",
        "DNT": "1",
        "Google-GA-Data": "event328",
        "Origin": "https://myfans.jp",
        "Referer": "https://myfans.jp/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": config.request.user_agent,
        **get_sec_ch_ua_dict(),
    }
