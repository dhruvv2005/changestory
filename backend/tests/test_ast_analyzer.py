import pytest
from app.analysis.ast_analyzer import (
    map_changed_lines_to_symbols,
    parse_python_source,
)


def test_parse_functions_classes_and_methods():
    code = """class OrderProcessor:
    def __init__(self, tax_rate):
        self.tax_rate = tax_rate

    def process(self, amount):
        return amount * (1.0 + self.tax_rate)

async def async_fetch():
    return 123

def standalone_func():
    pass
"""
    mod = parse_python_source(code, "example.py", module_prefix="example")
    assert not mod.has_syntax_error
    names = [s.name for s in mod.symbols]
    assert "OrderProcessor" in names
    assert "__init__" in names
    assert "process" in names
    assert "async_fetch" in names
    assert "standalone_func" in names

    proc = next(s for s in mod.symbols if s.name == "process")
    assert proc.symbol_type == "method"
    assert proc.parent_class == "OrderProcessor"
    assert proc.qualified_name == "example.OrderProcessor.process"

    afn = next(s for s in mod.symbols if s.name == "async_fetch")
    assert afn.symbol_type == "async_function"


def test_map_changed_lines_to_symbols():
    code = """# Header comment
def calculate_total(price, tax):
    tax_amt = price * tax
    return price + tax_amt

def other_func():
    pass
"""
    mod = parse_python_source(code, "calc.py", module_prefix="calc")
    # Change line 4 (inside calculate_total)
    changed_symbols, evidence, limits = map_changed_lines_to_symbols(mod, [4])
    assert len(changed_symbols) == 1
    assert changed_symbols[0].name == "calculate_total"
    assert changed_symbols[0].file_path == "calc.py"
    assert len(evidence) >= 1
    assert evidence[0].kind == "changed_line"


def test_syntax_error_graceful_handling():
    invalid_code = "def broken_syntax(:\n    pass"
    mod = parse_python_source(invalid_code, "broken.py")
    assert mod.has_syntax_error
    assert "syntax error" in (mod.error_message or "").lower()

    changed_symbols, evidence, limits = map_changed_lines_to_symbols(mod, [1])
    assert len(changed_symbols) == 0
    assert any("syntax error" in l.lower() for l in limits)


def test_parse_python_source_accepts_utf8_bom():
    mod = parse_python_source("\ufeffdef calculate_total(items):\n    return sum(items)\n", "calculator.py")

    assert not mod.has_syntax_error
    assert [symbol.name for symbol in mod.symbols] == ["calculate_total"]
