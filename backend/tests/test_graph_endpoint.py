"""Red-green: /api/graph must expose full node attributes (for the node
detail popover) and edge modes (exclude vs down-rank) — not just id/kind/name."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_graph_nodes_carry_full_attributes():
    data = client.get("/api/graph").json()
    by_id = {n["id"]: n for n in data["nodes"]}

    knee = by_id["joint:knee"]
    assert knee["kind"] == "joint"
    assert any(m["scheme"] == "snomedct" for m in knee["skos_mappings"])

    exercises = [n for n in data["nodes"] if n["kind"] == "exercise"]
    assert exercises and all("priority_tier" in n for n in exercises)
    assert all("is_bilateral" in n for n in exercises)


def test_graph_links_carry_contraindication_mode():
    data = client.get("/api/graph").json()
    contra = [link for link in data["links"] if link["rel"] == "contraindicated_for"]
    assert contra
    assert {link["mode"] for link in contra} <= {"exclude", "down_rank"}
    # non-contraindication links don't grow a spurious mode key
    assert all("mode" not in link for link in data["links"] if link["rel"] == "targets")
