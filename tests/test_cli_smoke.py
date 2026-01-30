import json

from dpw.__main__ import run


def test_cli_text_output_smoke(capsys):
    code = run(["200", "1000x2000", "scribe=50x50", "edge=3", "yield=80", "method=corner", "notch=none"])
    assert code == 0
    out = capsys.readouterr().out
    assert "total_dies=" in out
    assert "yield_dies=" in out


def test_cli_json_output_smoke(capsys):
    code = run(["--json", "200", "1000x2000", "scribe=50x50"])
    assert code == 0
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["total_dies"] > 0
    assert "parameters" in payload

