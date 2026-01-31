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
        "engineer",
        "developer",
        "backend",
        "frontend",
        "full-stack",
        "fullstack",
        "sre",
        "devops",
        "machine learning",
        "data engineer",
        "platform",
        "infrastructure",
        "web",
        "test",
        "programmer",
        "coding",
    ]

    title_lower = title.lower()
    return any(keyword in title_lower for keyword in keywords)
