from user_agents import parse
from typing import TypedDict


class UserAgentInfo(TypedDict):
    browser: str | None
    os: str | None
    device_type: str | None


def parse_user_agent(
    user_agent_string: str | None
) -> UserAgentInfo:
    """
    Parse raw user-agent string and extract browser, OS and device type.
    """

    if not user_agent_string:
        return {
            "browser": None,
            "os": None,
            "device_type": None
        }

    user_agent = parse(user_agent_string)

    # Browser
    if user_agent.browser.family:
        browser = user_agent.browser.family
    else:
        browser = None

    # Operating system
    if user_agent.os.family:
        os = user_agent.os.family
    else:
        os = None

    # Device classification
    if user_agent.is_mobile:
        device_type = "Mobile"

    elif user_agent.is_tablet:
        device_type = "Tablet"

    elif user_agent.is_pc:
        device_type = "Desktop"

    else:
        device_type = "Other"

    return {
        "browser": browser,
        "os": os,
        "device_type": device_type
    }