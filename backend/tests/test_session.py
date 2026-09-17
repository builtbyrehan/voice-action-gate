"""Session state tests — conversation state machine and session manager."""
from app.session.state import ConversationState, Phase, SessionManager


def test_new_session_starts_idle():
    state = ConversationState(session_id="test_1")
    assert state.phase == Phase.IDLE
    assert state.action_name is None
    assert state.evidence == []
    assert state.transcript == []


def test_session_manager_creates_new():
    mgr = SessionManager()
    state = mgr.get_or_create("s1")
    assert state.session_id == "s1"
    assert state.phase == Phase.IDLE


def test_session_manager_returns_same():
    mgr = SessionManager()
    s1 = mgr.get_or_create("s2")
    s2 = mgr.get_or_create("s2")
    assert s1 is s2


def test_session_manager_different_ids():
    mgr = SessionManager()
    s1 = mgr.get_or_create("a")
    s2 = mgr.get_or_create("b")
    assert s1 is not s2
    assert s1.session_id != s2.session_id
