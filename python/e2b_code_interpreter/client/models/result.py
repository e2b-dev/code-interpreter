from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.result_extra import ResultExtra
    from ..models.result_json import ResultJson


T = TypeVar("T", bound="Result")


@_attrs_define
class Result:
    """
    Attributes:
        text (Union[Unset, str]): Textual representation of the result
        html (Union[Unset, str]): HTML representation of the result
        markdown (Union[Unset, str]): Markdown representation of the result
        svg (Union[Unset, str]): SVG representation of the result
        png (Union[Unset, str]): PNG representation of the result
        jpeg (Union[Unset, str]): JPEG representation of the result
        pdf (Union[Unset, str]): PDF representation of the result
        latex (Union[Unset, str]): LaTeX representation of the result
        json (Union[Unset, ResultJson]): JSON representation of the result
        javascript (Union[Unset, str]): JavaScript representation of the result
        extra (Union[Unset, ResultExtra]): Extra representations of the result
        is_main_result (Union[Unset, bool]): Whether this is the main result of the cell
    """

    text: Union[Unset, str] = UNSET
    html: Union[Unset, str] = UNSET
    markdown: Union[Unset, str] = UNSET
    svg: Union[Unset, str] = UNSET
    png: Union[Unset, str] = UNSET
    jpeg: Union[Unset, str] = UNSET
    pdf: Union[Unset, str] = UNSET
    latex: Union[Unset, str] = UNSET
    json: Union[Unset, "ResultJson"] = UNSET
    javascript: Union[Unset, str] = UNSET
    extra: Union[Unset, "ResultExtra"] = UNSET
    is_main_result: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        text = self.text

        html = self.html

        markdown = self.markdown

        svg = self.svg

        png = self.png

        jpeg = self.jpeg

        pdf = self.pdf

        latex = self.latex

        json: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.json, Unset):
            json = self.json.to_dict()

        javascript = self.javascript

        extra: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.extra, Unset):
            extra = self.extra.to_dict()

        is_main_result = self.is_main_result

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if text is not UNSET:
            field_dict["text"] = text
        if html is not UNSET:
            field_dict["html"] = html
        if markdown is not UNSET:
            field_dict["markdown"] = markdown
        if svg is not UNSET:
            field_dict["svg"] = svg
        if png is not UNSET:
            field_dict["png"] = png
        if jpeg is not UNSET:
            field_dict["jpeg"] = jpeg
        if pdf is not UNSET:
            field_dict["pdf"] = pdf
        if latex is not UNSET:
            field_dict["latex"] = latex
        if json is not UNSET:
            field_dict["json"] = json
        if javascript is not UNSET:
            field_dict["javascript"] = javascript
        if extra is not UNSET:
            field_dict["extra"] = extra
        if is_main_result is not UNSET:
            field_dict["is_main_result"] = is_main_result

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.result_extra import ResultExtra
        from ..models.result_json import ResultJson

        d = src_dict.copy()
        text = d.pop("text", UNSET)

        html = d.pop("html", UNSET)

        markdown = d.pop("markdown", UNSET)

        svg = d.pop("svg", UNSET)

        png = d.pop("png", UNSET)

        jpeg = d.pop("jpeg", UNSET)

        pdf = d.pop("pdf", UNSET)

        latex = d.pop("latex", UNSET)

        _json = d.pop("json", UNSET)
        json: Union[Unset, ResultJson]
        if isinstance(_json, Unset):
            json = UNSET
        else:
            json = ResultJson.from_dict(_json)

        javascript = d.pop("javascript", UNSET)

        _extra = d.pop("extra", UNSET)
        extra: Union[Unset, ResultExtra]
        if isinstance(_extra, Unset):
            extra = UNSET
        else:
            extra = ResultExtra.from_dict(_extra)

        is_main_result = d.pop("is_main_result", UNSET)

        result = cls(
            text=text,
            html=html,
            markdown=markdown,
            svg=svg,
            png=png,
            jpeg=jpeg,
            pdf=pdf,
            latex=latex,
            json=json,
            javascript=javascript,
            extra=extra,
            is_main_result=is_main_result,
        )

        result.additional_properties = d
        return result

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
