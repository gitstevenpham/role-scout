"""Job filtering utilities."""


def is_engineering_role(title: str) -> bool:
    """
    Check if job title is a software engineering role.

    Args:
        title: Job title to check

    Returns:
        True if the title appears to be a software engineering role
    """
    keywords = [
        "software",
        # "engineer",
        # "developer",
        "backend",
        "frontend",
        "full-stack",
        "fullstack",
        # "data engineer",
        # "platform",
    ]

    blacklist = [
        "android",
        "ios",
        "mobile",
        "devops",
        "principal",
        "security",
        "staff"
    ]

    title_lower = title.lower()

    # Check if title contains blacklisted keywords
    if any(keyword in title_lower for keyword in blacklist):
        return False

    return any(keyword in title_lower for keyword in keywords)
