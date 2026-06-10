from __future__ import annotations

from typing import Any, TypeVar

ModelT = TypeVar("ModelT")


def validate_model(payload: dict[str, Any], model_cls: type[ModelT]) -> ModelT:
    try:
        return model_cls.model_validate(payload)
    except Exception as exc:
        raise ValueError(str(exc)) from exc
