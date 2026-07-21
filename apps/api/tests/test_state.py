import pytest
from pydantic import ValidationError
from app.core.state import OrbStateMachine, OrbState, OrbStateEvent

def test_orb_state_machine_initial_state():
    machine = OrbStateMachine()
    assert machine.current_state == OrbState.IDLE
    
    machine_custom = OrbStateMachine(initial_state=OrbState.ERROR)
    assert machine_custom.current_state == OrbState.ERROR

def test_orb_state_machine_valid_transition():
    machine = OrbStateMachine()
    event = machine.transition_to(OrbState.THINKING, reason="user_input")
    
    assert machine.current_state == OrbState.THINKING
    assert isinstance(event, OrbStateEvent)
    assert event.previous_state == OrbState.IDLE
    assert event.current_state == OrbState.THINKING
    assert event.reason == "user_input"
    assert event.timestamp is not None

def test_orb_state_machine_invalid_transition():
    machine = OrbStateMachine(initial_state=OrbState.RESPONDING)
    
    # RESPONDING cannot transition to LISTENING
    with pytest.raises(ValueError, match="Invalid state transition"):
        machine.transition_to(OrbState.LISTENING, reason="invalid_test")
        
    # State should remain unchanged
    assert machine.current_state == OrbState.RESPONDING

def test_orb_state_machine_no_op_transition():
    machine = OrbStateMachine(initial_state=OrbState.IDLE)
    
    event = machine.transition_to(OrbState.IDLE, reason="sync")
    assert machine.current_state == OrbState.IDLE
    assert event.previous_state == OrbState.IDLE
    assert event.current_state == OrbState.IDLE
    assert event.reason == "sync"

def test_orb_state_event_model():
    # Test valid model instantiation
    event = OrbStateEvent(
        previous_state=OrbState.IDLE,
        current_state=OrbState.THINKING,
        reason="test"
    )
    assert event.previous_state == OrbState.IDLE
    assert event.current_state == OrbState.THINKING
    assert event.reason == "test"
    assert isinstance(event.timestamp, str)
    
    # Test validation error on invalid state
    with pytest.raises(ValidationError):
        OrbStateEvent(
            previous_state="NOT_A_REAL_STATE",
            current_state=OrbState.THINKING,
            reason="test"
        )
