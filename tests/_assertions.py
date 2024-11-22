import httpx


def assert_unauthenticated_response(response: httpx.Response) -> None:
    assert response.status_code == 307
    assert response.headers["location"].startswith(
        "http://gitspatch.local/auth/login?return_to="
    )
    assert response.headers["gitspatch-redirect-reason"] == "auth_required"
