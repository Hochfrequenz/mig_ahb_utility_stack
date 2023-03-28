"""
module that (de)serializes AhbLocations to/from XML
"""
from typing import List, Union

import attrs

from maus.navigation import AhbLocation, AhbLocationLayer

try:
    import xmltodict
    from lxml import etree  # type:ignore[import]

    # pylint:disable=no-name-in-module
    from lxml.etree import _Element  # type:ignore[import]
except ImportError as import_error:
    import_error.msg += "; Did you install maus[xml]?"
    # lxml and xmlttodict are optional dependencies of maus but in this module, it is required
    raise


_AHB_LOCATION_LIST_XML_TAG_NAME = "ahbLocationLayers"
_AHB_LOCATION_XML_TAG_NAME = "ahbLocation"
_AHB_LOCATION_LAYER_XML_TAG_NAME = "ahbLocationLayer"


# pylint:disable=c-extension-no-member
def _create_null_element() -> _Element:
    """Create an element with a null value using the "xsi:nil" attribute"""
    # Ideally you add
    # xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    # to the xml root element
    null_element = etree.Element("null_element", attrib={"{xsi}nil": "true"})
    return null_element


# pylint:disable=c-extension-no-member
def to_xml_element(location: Union[AhbLocation, AhbLocationLayer]) -> etree.Element:
    """
    converts an AhbLocation or AhbLocationLayer to an XML element
    """
    dict_item: dict
    if isinstance(location, dict):
        dict_item = location
        result = etree.Element(_AHB_LOCATION_LAYER_XML_TAG_NAME)
    elif isinstance(location, AhbLocation):
        dict_item = attrs.asdict(location)
        result = etree.Element(_AHB_LOCATION_XML_TAG_NAME)
    elif isinstance(location, AhbLocationLayer):
        dict_item = attrs.asdict(location)
        result = etree.Element(_AHB_LOCATION_LAYER_XML_TAG_NAME)
    else:
        raise ValueError(f"Unexpected input {location}")
    for attr_name, attr_value in dict_item.items():
        if isinstance(attr_value, list):  # it can only be a AhbLocationLayer list
            subroot = etree.SubElement(result, attr_name)
            for sub_attr in attr_value:
                sub_elem = to_xml_element(sub_attr)
                subroot.append(sub_elem)
        else:
            if attr_value is None:
                etree.SubElement(result, attr_name, attrib={"{xsi}nil": "true"})
            else:
                elem = etree.SubElement(result, attr_name)
                elem.text = str(attr_value)
    return result


def to_xml_elements(locations: List[AhbLocation]) -> etree.Element:
    """
    converts multiple AhbLocations to an XML element
    """
    result = etree.Element(_AHB_LOCATION_LIST_XML_TAG_NAME)
    for location in locations:
        location_element = to_xml_element(location)
        result.append(location_element)
    return result


def _replace_nil_element_with_none(raw_dict: dict) -> dict:
    sanitized_values: dict = {}
    for key, value in raw_dict.items():
        if isinstance(value, dict) and any(
            _key.startswith("@ns") and _key.endswith(":nil") and _value == "true" for _key, _value in value.items()
        ):
            sanitized_values[key] = None
        else:
            sanitized_values[key] = value
    return sanitized_values


def _xml_dict_to_location(xml_dict: dict) -> AhbLocation:
    layers: List[AhbLocationLayer] = []
    layer_dicts = xml_dict["layers"][_AHB_LOCATION_LAYER_XML_TAG_NAME]
    for ahb_location_layer_dict in layer_dicts:
        sanitized_values = _replace_nil_element_with_none(ahb_location_layer_dict)
        layer = AhbLocationLayer(**sanitized_values)
        layers.append(layer)
    del xml_dict["layers"]
    sanitized_leftovers = _replace_nil_element_with_none(xml_dict)
    return AhbLocation(layers=layers, **sanitized_leftovers)


# pylint:disable=c-extension-no-member
def from_xml_element(xml: Union[str, _Element]) -> AhbLocation:
    """
    deserializes an AhbLocation from an etree element or str
    :param xml:
    :return:
    """
    if isinstance(xml, _Element):
        xml_str = etree.tostring(xml)
    else:
        xml_str = xml
    xml_dict = xmltodict.parse(xml_str)[_AHB_LOCATION_XML_TAG_NAME]
    return _xml_dict_to_location(xml_dict)


def from_xml_elements(xml: Union[str, _Element]) -> List[AhbLocation]:
    """
    deserializes multiple ahb locations
    """
    if isinstance(xml, _Element):
        xml_str = etree.tostring(xml)
    else:
        xml_str = xml
    xml_list = xmltodict.parse(xml_str)[_AHB_LOCATION_LIST_XML_TAG_NAME][_AHB_LOCATION_XML_TAG_NAME]
    return [_xml_dict_to_location(xml_dict) for xml_dict in xml_list]
