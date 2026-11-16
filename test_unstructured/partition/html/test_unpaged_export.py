"""Default HTML export retains content when page metadata is unavailable."""

from bs4 import BeautifulSoup

from unstructured.documents.elements import ElementMetadata, Text, Title
from unstructured.partition.html.convert import elements_to_html


def test_default_export_retains_a_document_without_page_numbers():
    elements = [Title("Heading", element_id="heading"), Text("Body", element_id="body")]

    soup = BeautifulSoup(elements_to_html(elements), "html.parser")

    assert soup.body.get_text(" ", strip=True) == "Heading Body"
    assert soup.find(id="heading") is not None
    assert soup.find(id="body") is not None
    assert soup.find(attrs={"data-page_number": True}) is None
    assert all(element.metadata.page_number is None for element in elements)


def test_mixed_page_metadata_retains_every_element_in_input_order():
    elements = [
        Text("First", metadata=ElementMetadata(page_number=1)),
        Text("Unpaged note"),
        Text("Last", metadata=ElementMetadata(page_number=2)),
    ]

    soup = BeautifulSoup(elements_to_html(elements), "html.parser")

    assert soup.body.get_text(" ", strip=True) == "First Unpaged note Last"
    assert soup.find(attrs={"data-page_number": True}) is None


def test_fully_paginated_documents_keep_page_containers():
    elements = [
        Text("First", metadata=ElementMetadata(page_number=1)),
        Text("Second", metadata=ElementMetadata(page_number=2)),
    ]

    soup = BeautifulSoup(elements_to_html(elements), "html.parser")

    assert len(soup.select("[data-page_number]")) == 2
    assert soup.body.get_text(" ", strip=True) == "First Second"


def test_explicit_flat_export_remains_supported():
    element = Text("Content", metadata=ElementMetadata(page_number=1))

    soup = BeautifulSoup(elements_to_html([element], no_group_by_page=True), "html.parser")

    assert soup.find(attrs={"data-page_number": True}) is None
    assert soup.body.get_text(strip=True) == "Content"


def test_empty_input_still_produces_an_empty_body():
    soup = BeautifulSoup(elements_to_html([]), "html.parser")

    assert soup.body.get_text(strip=True) == ""
