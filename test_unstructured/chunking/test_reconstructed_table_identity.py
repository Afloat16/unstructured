"""Reconstructing a split table preserves the original document identity."""

from unstructured.chunking.basic import chunk_elements
from unstructured.chunking.dispatch import reconstruct_table_from_chunks
from unstructured.documents.elements import ElementMetadata, Table, TableChunk, Text


def test_real_table_chunking_round_trip_preserves_identity_and_child_references():
    original = Table(
        "Alpha Beta Gamma Delta Epsilon Zeta Eta Theta",
        element_id="original-table",
        metadata=ElementMetadata(parent_id="section"),
    )
    child = Text("Table note", metadata=ElementMetadata(parent_id=original.id))
    chunks = chunk_elements([original], max_characters=15)
    assert len(chunks) > 1
    assert all(isinstance(chunk, TableChunk) for chunk in chunks)

    reconstructed = reconstruct_table_from_chunks(chunks)[0]

    assert reconstructed.id == original.id == child.metadata.parent_id
    assert reconstructed.metadata.parent_id == "section"
    assert reconstruct_table_from_chunks(chunks)[0].id == reconstructed.id


def test_each_reconstructed_group_retains_its_own_table_id():
    chunks = [
        TableChunk("B1", metadata=ElementMetadata(table_id="table-b", chunk_index=1)),
        TableChunk("A0", metadata=ElementMetadata(table_id="table-a", chunk_index=0)),
        TableChunk("B0", metadata=ElementMetadata(table_id="table-b", chunk_index=0)),
    ]

    tables = reconstruct_table_from_chunks(chunks)

    assert [(table.id, table.text) for table in tables] == [
        ("table-b", "B0 B1"),
        ("table-a", "A0"),
    ]


def test_reconstruction_clears_only_output_chunk_metadata():
    chunk = TableChunk(
        "Cell",
        metadata=ElementMetadata(table_id="table-id", chunk_index=0, parent_id="section"),
    )

    table = reconstruct_table_from_chunks([chunk])[0]

    assert table.metadata.table_id is None
    assert table.metadata.chunk_index is None
    assert table.metadata.parent_id == "section"
    assert chunk.metadata.table_id == "table-id"
    assert chunk.metadata.chunk_index == 0
