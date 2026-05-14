def test_project_scaffold_imports() -> None:
    import src

    assert src.__doc__ == "Search engine tool package."
