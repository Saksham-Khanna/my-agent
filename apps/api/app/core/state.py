from enum import Enum
from datetime import datetime, timezone
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class OrbState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    THINKING = "THINKING"
    RESPONDING = "RESPONDING"
    VISION = "VISION"
    EXECUTING = "EXECUTING"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"

class OrbStateEvent(BaseModel):
    previous_state: OrbState
    current_state: OrbState
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reason: str

# Define legal transitions from a given state to a set of valid next states.
VALID_TRANSITIONS = {
    OrbState.IDLE: {OrbState.LISTENING, OrbState.THINKING, OrbState.VISION, OrbState.EXECUTING, OrbState.ERROR},
    OrbState.LISTENING: {OrbState.TRANSCRIBING, OrbState.ERROR, OrbState.INTERRUPTED},
    OrbState.TRANSCRIBING: {OrbState.THINKING, OrbState.ERROR, OrbState.INTERRUPTED},
    OrbState.THINKING: {OrbState.RESPONDING, OrbState.ERROR, OrbState.INTERRUPTED},
    OrbState.RESPONDING: {OrbState.IDLE, OrbState.ERROR, OrbState.INTERRUPTED},
    OrbState.VISION: {OrbState.THINKING, OrbState.ERROR, OrbState.INTERRUPTED},
    OrbState.EXECUTING: {OrbState.IDLE, OrbState.ERROR, OrbState.INTERRUPTED},
    OrbState.INTERRUPTED: {OrbState.IDLE, OrbState.ERROR},
    OrbState.ERROR: {OrbState.IDLE},
}

class OrbStateMachine:
    def __init__(self, initial_state: OrbState = OrbState.IDLE):
        self._current_state = initial_state
        logger.debug(f"OrbStateMachine initialized with state: {self._current_state}")

    @property
    def current_state(self) -> OrbState:
        return self._current_state

    def transition_to(self, new_state: OrbState, reason: str = "") -> OrbStateEvent:
        """
        Validates and executes a state transition, returning a typed event.
        Raises ValueError if the transition is invalid.
        """
        if new_state == self._current_state:
            # Self-transitions are permitted but logged as no-ops. They return an event but the caller 
            # might choose not to broadcast it.
            logger.debug(f"No-op transition: {self._current_state} -> {new_state} (Reason: {reason})")
            return OrbStateEvent(
                previous_state=self._current_state,
                current_state=self._current_state,
                reason=reason
            )

        valid_next_states = VALID_TRANSITIONS.get(self._current_state, set())
        
        if new_state not in valid_next_states:
            err_msg = f"Invalid state transition: Cannot transition from {self._current_state} to {new_state}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        logger.info(f"State transition: {self._current_state} -> {new_state} (Reason: {reason})")
        
        event = OrbStateEvent(
            previous_state=self._current_state,
            current_state=new_state,
            reason=reason
        )
        
        self._current_state = new_state
        return event
