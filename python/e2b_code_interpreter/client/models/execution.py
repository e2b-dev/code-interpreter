from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.error import Error
    from ..models.logs import Logs
    from ..models.result import Result


T = TypeVar("T", bound="Execution")


@_attrs_define
class Execution:
    """
    Attributes:
        results (Union[Unset, List['Result']]):
        logs (Union[Unset, Logs]):
        error (Union[Unset, Error]):
        execution_count (Union[Unset, int]): Execution count of the cell.
    """

    results: Union[Unset, List["Result"]] = UNSET
    logs: Union[Unset, "Logs"] = UNSET
    error: Union[Unset, "Error"] = UNSET
    execution_count: Union[Unset, int] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        results: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.results, Unset):
            results = []
            for results_item_data in self.results:
                results_item = results_item_data.to_dict()
                results.append(results_item)

        logs: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.logs, Unset):
            logs = self.logs.to_dict()

        error: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.error, Unset):
            error = self.error.to_dict()

        execution_count = self.execution_count

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if results is not UNSET:
            field_dict["results"] = results
        if logs is not UNSET:
            field_dict["logs"] = logs
        if error is not UNSET:
            field_dict["error"] = error
        if execution_count is not UNSET:
            field_dict["execution_count"] = execution_count

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.error import Error
        from ..models.logs import Logs
        from ..models.result import Result

        d = src_dict.copy()
        results = []
        _results = d.pop("results", UNSET)
        for results_item_data in _results or []:
            results_item = Result.from_dict(results_item_data)

            results.append(results_item)

        _logs = d.pop("logs", UNSET)
        logs: Union[Unset, Logs]
        if isinstance(_logs, Unset):
            logs = UNSET
        else:
            logs = Logs.from_dict(_logs)

        _error = d.pop("error", UNSET)
        error: Union[Unset, Error]
        if isinstance(_error, Unset):
            error = UNSET
        else:
            error = Error.from_dict(_error)

        execution_count = d.pop("execution_count", UNSET)

        execution = cls(
            results=results,
            logs=logs,
            error=error,
            execution_count=execution_count,
        )

        execution.additional_properties = d
        return execution

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
