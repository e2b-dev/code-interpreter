from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Error")


@_attrs_define
class Error:
    """
    Attributes:
        name (Union[Unset, str]): Name of the exception
        value (Union[Unset, str]): Value of the exception
        traceback_raw (Union[Unset, List[str]]): List of strings representing the traceback
        code (Union[Unset, int]): Error code
        message (Union[Unset, str]): Error
    """

    name: Union[Unset, str] = UNSET
    value: Union[Unset, str] = UNSET
    traceback_raw: Union[Unset, List[str]] = UNSET
    code: Union[Unset, int] = UNSET
    message: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name

        value = self.value

        traceback_raw: Union[Unset, List[str]] = UNSET
        if not isinstance(self.traceback_raw, Unset):
            traceback_raw = self.traceback_raw

        code = self.code

        message = self.message

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if value is not UNSET:
            field_dict["value"] = value
        if traceback_raw is not UNSET:
            field_dict["traceback_raw"] = traceback_raw
        if code is not UNSET:
            field_dict["code"] = code
        if message is not UNSET:
            field_dict["message"] = message

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        name = d.pop("name", UNSET)

        value = d.pop("value", UNSET)

        traceback_raw = cast(List[str], d.pop("traceback_raw", UNSET))

        code = d.pop("code", UNSET)

        message = d.pop("message", UNSET)

        error = cls(
            name=name,
            value=value,
            traceback_raw=traceback_raw,
            code=code,
            message=message,
        )

        error.additional_properties = d
        return error

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
