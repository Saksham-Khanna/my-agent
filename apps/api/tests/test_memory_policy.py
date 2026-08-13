import pytest
from app.core.memory_policy import DefaultRetrievalPolicy


@pytest.mark.anyio
async def test_policy_skips_actions_mode():
    policy = DefaultRetrievalPolicy()
    decision = await policy.decide("actions", "run system info", [])
    assert decision.should_query is False


@pytest.mark.anyio
async def test_policy_skips_screen_mode():
    policy = DefaultRetrievalPolicy()
    decision = await policy.decide("screen", "what do you see?", [])
    assert decision.should_query is False


@pytest.mark.anyio
async def test_policy_skips_short_text():
    policy = DefaultRetrievalPolicy()
    decision = await policy.decide("talk", "hi", [])
    assert decision.should_query is False


@pytest.mark.anyio
async def test_policy_skips_ignore_memory_keyword():
    policy = DefaultRetrievalPolicy()
    decision = await policy.decide("talk", "please ignore memory for this", [])
    assert decision.should_query is False


@pytest.mark.anyio
async def test_policy_always_queries_talk():
    policy = DefaultRetrievalPolicy()
    decision = await policy.decide("talk", "what did I say about Python?", [])
    assert decision.should_query is True
    assert decision.query_text == "what did I say about Python?"
    assert decision.max_results == 5


@pytest.mark.anyio
async def test_policy_always_queries_memory():
    policy = DefaultRetrievalPolicy()
    decision = await policy.decide("memory", "remember my favorite color", [])
    assert decision.should_query is True


@pytest.mark.anyio
async def test_policy_conditional_vision_with_keyword():
    policy = DefaultRetrievalPolicy()
    decision = await policy.decide("vision", "remember what I showed you last time", [])
    assert decision.should_query is True


@pytest.mark.anyio
async def test_policy_conditional_vision_without_keyword():
    policy = DefaultRetrievalPolicy()
    decision = await policy.decide("vision", "describe this image", [])
    assert decision.should_query is False


@pytest.mark.anyio
async def test_policy_conditional_files_with_keyword():
    policy = DefaultRetrievalPolicy()
    decision = await policy.decide("files", "previously I asked about architecture", [])
    assert decision.should_query is True


@pytest.mark.anyio
async def test_policy_skips_empty_text():
    policy = DefaultRetrievalPolicy()
    decision = await policy.decide("talk", "", [])
    assert decision.should_query is False
