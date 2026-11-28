from database import engine


def test_the_app_checks_the_database_link_still_works_before_using_it():
    # Neon's free plan suspends the database after 5 idle minutes, which kills
    # pooled connections; pre-ping makes the first request after that reconnect
    # instead of hang.
    assert engine.pool._pre_ping is True
