from typing import List, Optional


class AuthorizationDomainService:
    """
    Pure business rule enforcement.
    No database access. No infrastructure.
    """

    def is_cross_domain_violation(self, domain: Optional[List[str]]) -> bool:
        """
        Block analytics requests spanning more than 3 unrelated domains.
        """
        if not domain:
            return False
        return len(domain) > 3
