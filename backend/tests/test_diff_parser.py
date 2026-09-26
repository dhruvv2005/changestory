import pytest
from app.analysis.diff_parser import clean_file_path, parse_unified_diff


def test_clean_file_path():
    assert clean_file_path("a/path/to/file.py") == "path/to/file.py"
    assert clean_file_path("b/another\\file.py") == "another/file.py"
    assert clean_file_path('"a/quoted/file.py"') == "quoted/file.py"


def test_parse_single_file_modified():
    diff = """--- a/changestory_sample/calculator.py
+++ b/changestory_sample/calculator.py
@@ -4,3 +4,4 @@
 def calculate_total(price: float, tax_rate: float) -> float:
     \"\"\"Calculate the final total price including tax.\"\"\"
-    return price + (price * tax_rate)
+    tax = price * tax_rate
+    return price + tax + 5.0
"""
    files, limits = parse_unified_diff(diff)
    assert len(files) == 1
    f = files[0]
    assert f.file_path == "changestory_sample/calculator.py"
    assert f.status == "modified"
    assert f.lines_added == 2
    assert f.lines_deleted == 1
    assert 6 in f.changed_lines or 7 in f.changed_lines
    assert not any("error" in lim.lower() for lim in limits)


def test_parse_multi_file():
    diff = """--- a/file_a.py
+++ b/file_a.py
@@ -1,2 +1,3 @@
+line 0
 line 1
 line 2
--- a/file_b.py
+++ b/file_b.py
@@ -10,2 +10,1 @@
-removed line
 preserved line
"""
    files, limits = parse_unified_diff(diff)
    assert len(files) == 2
    paths = [f.file_path for f in files]
    assert "file_a.py" in paths
    assert "file_b.py" in paths


def test_parse_added_file():
    diff = """--- /dev/null
+++ b/new_module.py
@@ -0,0 +1,5 @@
+def brand_new():
+    return 42
"""
    files, limits = parse_unified_diff(diff)
    assert len(files) == 1
    assert files[0].file_path == "new_module.py"
    assert files[0].status == "added"
    assert files[0].lines_added == 2


def test_parse_deleted_file():
    diff = """--- a/obsolete.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def dead_code():
-    pass
"""
    files, limits = parse_unified_diff(diff)
    assert len(files) == 1
    assert files[0].file_path == "obsolete.py"
    assert files[0].status == "deleted"
    assert files[0].lines_deleted == 2


def test_parse_empty_diff():
    files, limits = parse_unified_diff("")
    assert len(files) == 0
    assert any("empty" in l.lower() for l in limits)


def test_parse_malformed_diff():
    malformed = "Just some text without diff headers\nRandom line"
    files, limits = parse_unified_diff(malformed)
    assert len(files) == 0
    assert len(limits) > 0
