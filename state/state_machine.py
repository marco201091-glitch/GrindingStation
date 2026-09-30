from __future__ import annotations

import re
from collections import deque
from enum import Enum


class BotState(str, Enum):
    HOME = "HOME"
    PLAY_MENU = "PLAY_MENU"
    FIND_MATCH = "FIND_MATCH"
    HISTORIC = "HISTORIC"
    MY_DECKS = "MY_DECKS"
    IN_GAME = "IN_GAME"
    OPTIONS = "OPTIONS"
    STORE = "STORE"
    UNKNOWN = "UNKNOWN"


_SCENE_MAP = {
    "home": BotState.HOME,
    "frontdoor": BotState.HOME,
    "mainmenu": BotState.HOME,
    "play": BotState.PLAY_MENU,
    "playblade": BotState.PLAY_MENU,
    "matchmaking": BotState.FIND_MATCH,
    "decks": BotState.MY_DECKS,
    "collection": BotState.MY_DECKS,
    "store": BotState.STORE,
    "options": BotState.OPTIONS,
    "historic": BotState.HISTORIC,
}


def _latest_state_event(text: str) -> BotState | None:
    """Latest explicit transition; None means there is no state evidence.

    Deck names, quest payloads and format lists contain menu words too. They
    must never change navigation state or outweigh a later MainNav event.
    UNKNOWN is an actual transition (completion/loading), distinct from None.
    """
    lowered = text.lower()
    events = [
        (lowered.rfind(marker), state)
        for marker, state in (
            ("gremessagetype_gamestatemessage", BotState.IN_GAME),
            ("mainnav load in", BotState.HOME),
            ("matchgameroomstatetype_matchcompleted", BotState.UNKNOWN),
        )
    ]
    for match in re.finditer(r'"toSceneName"\s*:\s*"([^"]+)"', text):
        scene = match.group(1).strip().lower()
        state = next(
            (_SCENE_MAP[key] for key in sorted(_SCENE_MAP, key=len, reverse=True)
             if key in scene),
            BotState.UNKNOWN,
        )
        events.append((match.start(), state))
    position, state = max(events, key=lambda event: event[0])
    return state if position >= 0 else None


def get_state_from_playerlog(log_tail: str) -> BotState:
    return _latest_state_event(str(log_tail or "")) or BotState.UNKNOWN


def should_act(
    state: BotState,
    pending_message_count: int,
    decision_player_ok: bool,
    stack_present: bool,
) -> bool:
    if state == BotState.UNKNOWN:
        return False
    if int(pending_message_count or 0) > 0:
        return False
    if stack_present and not decision_player_ok:
        return False
    return True


class PlayerLogStateTracker:
    def __init__(self, max_lines: int = 400) -> None:
        self._lines: deque[str] = deque(maxlen=max(50, int(max_lines)))
        self._last_state: BotState = BotState.UNKNOWN

    def push_line(self, line: str) -> None:
        text = str(line or "").strip()
        if not text:
            return
        self._lines.append(text)
        # Parse only new input. Unrelated traffic cannot erase an explicit
        # transition merely because its line falls out of the diagnostic tail.
        state = _latest_state_event(text)
        if state is not None:
            self._last_state = state

    def get_state(self) -> BotState:
        return self._last_state

    def get_tail(self, max_lines: int = 120) -> str:
        count = max(1, int(max_lines))
        return "\n".join(list(self._lines)[-count:])
