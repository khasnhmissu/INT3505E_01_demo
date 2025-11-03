import unittest

from flask import json

from openapi_server.models.create_product201_response import CreateProduct201Response  # noqa: E501
from openapi_server.models.delete_product200_response import DeleteProduct200Response  # noqa: E501
from openapi_server.models.error import Error  # noqa: E501
from openapi_server.models.get_all_products200_response import GetAllProducts200Response  # noqa: E501
from openapi_server.models.get_product_by_id200_response import GetProductById200Response  # noqa: E501
from openapi_server.models.product_input import ProductInput  # noqa: E501
from openapi_server.models.update_product200_response import UpdateProduct200Response  # noqa: E501
from openapi_server.test import BaseTestCase


class TestProductsController(BaseTestCase):
    """ProductsController integration test stubs"""

    def test_create_product(self):
        """Test case for create_product

        Tạo product mới
        """
        product_input = {"price":1200.5,"name":"Laptop Dell XPS 13","stock":15}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/products',
            method='POST',
            headers=headers,
            data=json.dumps(product_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_product(self):
        """Test case for delete_product

        Xóa product
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/products/{product_id}'.format(product_id=1),
            method='DELETE',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_all_products(self):
        """Test case for get_all_products

        Lấy danh sách tất cả products
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/products',
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_get_product_by_id(self):
        """Test case for get_product_by_id

        Lấy thông tin 1 product theo ID
        """
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/products/{product_id}'.format(product_id=1),
            method='GET',
            headers=headers)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_product(self):
        """Test case for update_product

        Cập nhật thông tin product
        """
        product_input = {"price":1200.5,"name":"Laptop Dell XPS 13","stock":15}
        headers = { 
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = self.client.open(
            '/products/{product_id}'.format(product_id=1),
            method='PUT',
            headers=headers,
            data=json.dumps(product_input),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
