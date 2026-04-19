import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from main import app
import database_models

client = TestClient(app)


def make_mock_product(id=1, name="Phone", description="Budget phone", price=99.0, quantity=10):
    """Helper to create a mock Product DB object."""
    product = MagicMock(spec=database_models.Product)
    product.id = id
    product.name = name
    product.description = description
    product.price = price
    product.quantity = quantity
    return product


def mock_db():
    """Returns a mock DB session."""
    return MagicMock()


def override_get_db():
    yield mock_db()


# --- GET / ---

def test_greet():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()


# --- GET /products ---

def test_get_all_products_returns_list():
    mock_product = make_mock_product()
    db = MagicMock()
    db.query.return_value.all.return_value = [mock_product]

    response = client.get("/products")
    assert response.status_code == 200


def test_get_all_products_empty():
    db = MagicMock()
    db.query.return_value.all.return_value = []

    response = client.get("/products")
    assert response.status_code == 200
    assert response.json() == []


# --- GET /products/{id} ---

def test_get_product_by_id_found():
    mock_product = make_mock_product(id=1, name="Phone")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_product

    response = client.get("/products/1")
    assert response.status_code == 200


def test_get_product_by_id_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/products/999")
    assert response.status_code == 200
    assert response.json() == "product not found"


# --- POST /products ---

def test_add_product_success():
    db = MagicMock()

    payload = {"id": 1, "name": "Phone", "description": "Budget phone", "price": 99.0, "quantity": 10}
    response = client.post("/products", json=payload)

    assert response.status_code == 200
    assert response.json()["name"] == "Phone"
    assert response.json()["price"] == 99.0
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_add_product_with_zero_price():
    db = MagicMock()

    payload = {"id": 2, "name": "Freebie", "description": "Free item", "price": 0.0, "quantity": 5}
    response = client.post("/products", json=payload)

    assert response.status_code == 200
    assert response.json()["price"] == 0.0


def test_add_product_missing_field():
    db = MagicMock()

    # Missing 'quantity'
    payload = {"id": 3, "name": "Pen", "description": "Blue pen", "price": 1.99}
    response = client.post("/products", json=payload)

    assert response.status_code == 422  # Unprocessable Entity


# --- PUT /products ---

def test_update_product_success():
    mock_product = make_mock_product(id=1, name="Phone")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_product

    payload = {"id": 1, "name": "Smartphone", "description": "Updated", "price": 149.0, "quantity": 5}
    response = client.put("/products?id=1", json=payload)

    assert response.status_code == 200
    assert response.json() == "Product updated"
    assert mock_product.name == "Smartphone"
    assert mock_product.price == 149.0
    db.commit.assert_called_once()


def test_update_product_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    payload = {"id": 999, "name": "Ghost", "description": "N/A", "price": 0.0, "quantity": 0}
    response = client.put("/products?id=999", json=payload)

    assert response.status_code == 200
    assert response.json() == "No product found"
    db.commit.assert_not_called()


# --- DELETE /products ---

def test_delete_product_success():
    mock_product = make_mock_product(id=1)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_product

    response = client.delete("/products?id=1")

    assert response.status_code == 200
    assert response.json() == "product deleted"
    db.delete.assert_called_once_with(mock_product)
    db.commit.assert_called_once()


def test_delete_product_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    response = client.delete("/products?id=999")

    assert response.status_code == 200
    assert response.json() == "No product found"
    db.delete.assert_not_called()
    db.commit.assert_not_called()
