from database import engine


def test_engine_checks_connections_before_use():
    # Neon's free plan suspends the database after 5 idle minutes, which kills
    # pooled connections; pre-ping makes the first request after that reconnect
    # instead of hang.
    assert engine.pool._pre_ping is True
