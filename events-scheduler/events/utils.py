from enum import Enum
from typing import Dict


class EventListUserTypeEnum(Enum):
    """Event List User Enum

    An Enum responsible for determining the right endpoint for /events/view.

    Attributes:
        ALL (str): represents the /events/view/all endpoint where all upcoming events are returned
        CREATOR (str): represents the /events/view/creator endpoint where all events created by
         the authenticated request user are returned
    """
    ALL = 'all'
    CREATOR = 'creator'

    @classmethod
    def get_mapping(cls) -> Dict[str, "EventListUserTypeEnum"]:
        """Get Mapping

        Helper method for returning a dict mapping to speedup searching.
        """
        return {
            cls.ALL.value: cls.ALL,
            cls.CREATOR.value: cls.CREATOR
        }
