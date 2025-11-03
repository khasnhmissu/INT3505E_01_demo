import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.create_product201_response import CreateProduct201Response  # noqa: E501
from openapi_server.models.delete_product200_response import DeleteProduct200Response  # noqa: E501
from openapi_server.models.error import Error  # noqa: E501
from openapi_server.models.get_all_products200_response import GetAllProducts200Response  # noqa: E501
from openapi_server.models.get_product_by_id200_response import GetProductById200Response  # noqa: E501
from openapi_server.models.product_input import ProductInput  # noqa: E501
from openapi_server.models.update_product200_response import UpdateProduct200Response  # noqa: E501
from openapi_server import util


def create_product(body):  # noqa: E501
    """Tạo product mới

     # noqa: E501

    :param product_input: 
    :type product_input: dict | bytes

    :rtype: Union[CreateProduct201Response, Tuple[CreateProduct201Response, int], Tuple[CreateProduct201Response, int, Dict[str, str]]
    """
    product_input = body
    if connexion.request.is_json:
        product_input = ProductInput.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def delete_product(product_id):  # noqa: E501
    """Xóa product

     # noqa: E501

    :param product_id: ID của product cần xóa
    :type product_id: int

    :rtype: Union[DeleteProduct200Response, Tuple[DeleteProduct200Response, int], Tuple[DeleteProduct200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_all_products():  # noqa: E501
    """Lấy danh sách tất cả products

     # noqa: E501


    :rtype: Union[GetAllProducts200Response, Tuple[GetAllProducts200Response, int], Tuple[GetAllProducts200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_product_by_id(product_id):  # noqa: E501
    """Lấy thông tin 1 product theo ID

     # noqa: E501

    :param product_id: ID của product cần lấy
    :type product_id: int

    :rtype: Union[GetProductById200Response, Tuple[GetProductById200Response, int], Tuple[GetProductById200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def update_product(product_id, body):  # noqa: E501
    """Cập nhật thông tin product

     # noqa: E501

    :param product_id: ID của product cần cập nhật
    :type product_id: int
    :param product_input: 
    :type product_input: dict | bytes

    :rtype: Union[UpdateProduct200Response, Tuple[UpdateProduct200Response, int], Tuple[UpdateProduct200Response, int, Dict[str, str]]
    """
    product_input = body
    if connexion.request.is_json:
        product_input = ProductInput.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
