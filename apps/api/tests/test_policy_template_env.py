from promptshield.api import policy_store


def test_resolve_policy_template_env(monkeypatch, tmp_path):
    data = tmp_path / "policy_data"
    data.mkdir()
    (data / "active_policy.yml").write_text("version: 99\nsources: {}\n", encoding="utf-8")
    monkeypatch.setenv("PROMPTSHIELD_POLICY_DIR", str(data))
    monkeypatch.delenv("PROMPTSHIELD_POLICY", raising=False)
    assert policy_store.resolve_policy_path() == data / "active_policy.yml"
    monkeypatch.setenv("PROMPTSHIELD_POLICY", "template")
    assert policy_store.resolve_policy_path() == policy_store.default_policy_path()


def test_policy_dir_isolation_does_not_touch_repo(monkeypatch, tmp_path):
    data = tmp_path / "isolated"
    monkeypatch.setenv("PROMPTSHIELD_POLICY_DIR", str(data))
    monkeypatch.delenv("PROMPTSHIELD_POLICY", raising=False)
    meta = policy_store.save_policy({"version": 1, "sources": {}}, note="test")
    assert (data / "active_policy.yml").exists()
    assert meta["version"] >= 1
