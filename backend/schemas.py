from uuid import UUID
from dataclasses import dataclass


@dataclass
class AnnotatedFeatureInput ():
    type: str
    content: str
    xpath: str


@dataclass
class AnnotatedFeatureOutput ():
    id: UUID
    type: str
    xpath: str


@dataclass
class CartInput():
    provider: str
    language: str
    year: int
    created_by: str
    batch_size: int = 25


@dataclass
class CartOutput():
    id: UUID | None
    serp_ids: list[UUID]
    total: int


@dataclass
class AnnotationInput():
    cart_id: UUID
    features: list[AnnotatedFeatureInput]
