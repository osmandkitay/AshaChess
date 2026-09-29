"""HTTP API: the full game flow as the frontend uses it."""

PROMOTION_LINE = ["a2a4", "h7h5", "a4a5", "h5h4", "a5a6", "h4h3", "a6b7", "h3g2"]
SCHOLARS_MATE = ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"]


def play(client, *moves):
    response = None
    for uci in moves:
        response = client.post("/api/move", json={"move": uci})
        assert response.status_code == 200, (uci, response.get_json())
    return response.get_json()


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"ASHA CHESS" in response.data


def test_initial_state(client):
    state = client.get("/api/state").get_json()
    assert state["turn"] == "white"
    assert len(state["pieces"]) == 32 and state["pieces"]["e1"] == "K"
    assert len(state["legalMoves"]) == 34
    kinds = [m["kind"] for m in state["legalMoves"]]
    assert kinds.count("quiet") == 20 and kinds.count("pawn_diagonal") == 14 and len(set(kinds)) == 2
    assert state["history"] == [] and state["lastMove"] is None
    assert state["gameOver"] is False and state["result"] is None
    assert state["check"] is False and state["checkSquare"] is None
    assert state["claimableDraws"] == []


def test_move_updates_state_and_persists_in_session(client):
    state = play(client, "e2e4")
    assert state["turn"] == "black"
    assert state["pieces"].get("e4") == "P" and "e2" not in state["pieces"]
    assert state["lastMove"] == {
        "uci": "e2e4", "from": "e2", "to": "e4", "kind": "quiet", "capture": False, "promotion": None,
        "ply": 1, "color": "white", "piece": "P", "captured": None, "notation": "e4",
        "check": False, "checkmate": False,
    }  # fmt: skip
    assert client.get("/api/state").get_json() == state


def test_asha_moves_carry_metadata(client):
    state = play(client, "e2e4", "d7d5")
    moves = {m["uci"]: m for m in state["legalMoves"]}
    assert moves["e4f4"]["kind"] == "pawn_lateral" and moves["e4f4"]["capture"] is False
    assert moves["e4d5"]["kind"] == "capture" and moves["e4d5"]["capture"] is True
    assert moves["e4f5"]["kind"] == "pawn_diagonal" and moves["e4f5"]["capture"] is False
    assert not {"e4e3", "e4d3", "e4f3"} & set(moves)
    state = play(client, "e4f4", "g8f6", "g1e2", "f6e6")
    assert [h["notation"] for h in state["history"]] == ["e4", "d5", "e4~f4", "Nf6", "Ne2", "Nf6~e6"]
    assert state["lastMove"]["kind"] == "kings_step"
    state = play(client, "f4g5")
    assert state["lastMove"]["kind"] == "pawn_diagonal" and state["lastMove"]["notation"] == "f4~g5"
    assert state["lastMove"]["capture"] is False and state["lastMove"]["captured"] is None


def test_sideways_pawn_step_spends_double_step_across_requests(client):
    state = play(client, "e2e4", "b8c6", "e4e5", "c6b8", "d2e2")
    assert state["halfmoveClock"] == 0
    assert state["fen"].endswith(" ABCFGHabcdefgh")
    state = play(client, "b8c6")
    moves = {m["uci"] for m in state["legalMoves"]}
    assert "e2e3" in moves and "e2e4" not in moves and "c2c4" in moves
    assert client.post("/api/move", json={"move": "e2e4"}).status_code == 400


def test_capture(client):
    state = play(client, "e2e4", "d7d5", "e4d5")
    assert state["lastMove"]["capture"] is True
    assert state["lastMove"]["captured"] == "P"
    assert state["lastMove"]["notation"] == "exd5"


def test_check(client):
    state = play(client, "e2e4", "f7f6", "d1h5")
    assert state["check"] is True and state["checkSquare"] == "e8"
    assert state["lastMove"]["notation"] == "Qh5+"
    assert all(m["from"] in ("e8", "g7", "g8", "f8") or m["to"] in ("g6", "f7") for m in state["legalMoves"])


def test_illegal_move_is_rejected_with_state(client):
    for bad in ("e2e5", "e2c3", "e1e2", "nonsense", "e7e5"):
        response = client.post("/api/move", json={"move": bad})
        assert response.status_code == 400
        body = response.get_json()
        assert "error" in body and body["state"]["history"] == []


def test_pawn_cannot_move_backward_through_api(client):
    play(client, "e2e4", "a7a6")
    assert client.post("/api/move", json={"move": "e4e3"}).status_code == 400
    assert client.post("/api/move", json={"move": "e4d3"}).status_code == 400
    assert client.post("/api/move", json={"move": "e4f3"}).status_code == 400


def test_malformed_requests(client):
    assert client.post("/api/move", data="not json", content_type="application/json").status_code == 400
    assert client.post("/api/move", json={}).status_code == 400
    assert client.post("/api/move", json={"move": 42}).status_code == 400
    assert client.post("/api/move", json=["e2e4"]).status_code == 400
    assert client.post("/api/claim-draw", json=["threefold_repetition"]).status_code == 400


def test_promotion_requires_choice_and_supports_underpromotion(client):
    state = play(client, *PROMOTION_LINE)
    to_a8 = [m for m in state["legalMoves"] if m["from"] == "b7" and m["to"] == "a8"]
    assert sorted(m["promotion"] for m in to_a8) == ["b", "n", "q", "r"]
    assert all(m["uci"] == "b7a8" + m["promotion"] for m in to_a8)

    assert client.post("/api/move", json={"move": "b7a8"}).status_code == 400
    state = play(client, "b7a8n")
    assert state["pieces"]["a8"] == "N"
    assert state["lastMove"]["notation"] == "bxa8=N"
    assert state["lastMove"]["promotion"] == "n" and state["lastMove"]["captured"] == "R"

    state = play(client, "g2h1q")
    assert state["pieces"]["h1"] == "q"
    assert state["lastMove"]["notation"] == "gxh1=Q"


def test_checkmate_ends_the_game(client):
    state = play(client, *SCHOLARS_MATE)
    assert state["gameOver"] is True
    assert state["result"] == {"termination": "checkmate", "winner": "white"}
    assert state["legalMoves"] == []
    assert state["lastMove"]["notation"] == "Qxf7#" and state["lastMove"]["checkmate"] is True
    response = client.post("/api/move", json={"move": "e8e7"})
    assert response.status_code == 400
    assert response.get_json()["state"]["gameOver"] is True


def test_draw_claim(client):
    assert client.post("/api/claim-draw", json={}).status_code == 400
    state = play(client, *["g1f3", "g8f6", "f3g1", "f6g8"] * 2)
    assert state["claimableDraws"] == ["threefold_repetition"]
    assert state["gameOver"] is False
    response = client.post("/api/claim-draw", json={"reason": "threefold_repetition"})
    assert response.status_code == 200
    state = response.get_json()
    assert state["result"] == {"termination": "threefold_repetition", "winner": None}
    assert state["legalMoves"] == [] and state["claimableDraws"] == []
    assert client.get("/api/state").get_json()["gameOver"] is True
    assert client.post("/api/move", json={"move": "g1f3"}).status_code == 400
    # A draw never gets mate notation.
    assert not any(h["notation"].endswith("#") for h in state["history"])


def test_reset_returns_fresh_state(client):
    play(client, *SCHOLARS_MATE)
    response = client.post("/api/reset")
    assert response.status_code == 200
    state = response.get_json()
    assert state["history"] == [] and state["gameOver"] is False and len(state["legalMoves"]) == 34
    assert client.get("/api/state").get_json() == state


def test_sessions_are_isolated(client):
    play(client, "e2e4")
    other = client.application.test_client()
    assert other.get("/api/state").get_json()["history"] == []


def test_invalid_session_falls_back_to_new_game(client):
    with client.session_transaction() as session:
        session["moves"] = "e2e4 e2e4"
    state = client.get("/api/state").get_json()
    assert state["history"] == []
    with client.session_transaction() as session:
        assert "moves" not in session


def test_forged_cookie_is_ignored(client):
    play(client, "e2e4")
    client.set_cookie("session", "forged.value.here", domain="localhost")
    assert client.get("/api/state").get_json()["history"] == []
