from app.rag.chunker import CodeAwareChunker

def test_code_aware_chunker_preserves_lines():
    chunker = CodeAwareChunker(target_chunk_lines=10, overlap_lines=2)
    code = "\n".join([f"line_{i} = {i}" for i in range(1, 35)])
    
    chunks = chunker.chunk_file("test.py", code, language="Python")
    assert len(chunks) >= 3
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 10
    assert "line_1" in chunks[0]["content"]

def test_chunker_with_ast_entities():
    chunker = CodeAwareChunker()
    code = (
        "def func_a():\n"
        "    return 1\n\n"
        "def func_b():\n"
        "    return 2\n"
    )
    entities = [
        {"name": "func_a", "entity_type": "function", "start_line": 1, "end_line": 2},
        {"name": "func_b", "entity_type": "function", "start_line": 4, "end_line": 5},
    ]
    chunks = chunker.chunk_file("math.py", code, language="Python", entities=entities)
    assert len(chunks) == 2
    assert chunks[0]["entity_name"] == "func_a"
    assert chunks[1]["entity_name"] == "func_b"
