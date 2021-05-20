from typing import Tuple, Optional, Type, Set
import warnings

from optimade.models.entries import EntryResource

__all__ = ("BaseResourceMapper",)


class classproperty(property):
    """A simple extension of the property decorator that binds to types
    rather than instances.

    Modelled on this [StackOverflow answer](https://stackoverflow.com/a/5192374)
    with some tweaks to allow mkdocstrings to do its thing.

    """

    def __init__(self, func):
        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__
        self.__wrapped__ = func

    def __get__(self, _, owner):
        return self.__wrapped__(owner)


class BaseResourceMapper:
    """
    Generic Resource Mapper that defines and performs the mapping
    between objects in the database and the resource objects defined by
    the specification.

    Attributes:
        ALIASES: a tuple of aliases between
            OPTIMADE field names and the field names in the database ,
            e.g. `(("elements", "custom_elements_field"))`.
        LENGTH_ALIASES: a tuple of aliases between
            a field name and another field that defines its length, to be used
            when querying, e.g. `(("elements", "nelements"))`.
            e.g. `(("elements", "custom_elements_field"))`.
        ENTRY_RESOURCE_CLASS: The entry type that this mapper corresponds to.
        PROVIDER_FIELDS: a tuple of extra field names that this
            mapper should support when querying with the database prefix.
        TOP_LEVEL_NON_ATTRIBUTES_FIELDS: the set of top-level
            field names common to all endpoints.

    """

    try:
        from optimade.server.data import (
            providers as PROVIDERS,
        )  # pylint: disable=no-name-in-module
    except (ImportError, ModuleNotFoundError):
        PROVIDERS = {}

    KNOWN_PROVIDER_PREFIXES: Set[str] = set(
        prov["id"] for prov in PROVIDERS.get("data", [])
    )
    ALIASES: Tuple[Tuple[str, str]] = ()
    LENGTH_ALIASES: Tuple[Tuple[str, str]] = ()
    PROVIDER_FIELDS: Tuple[str] = ()
    ENTRY_RESOURCE_CLASS: Type[EntryResource] = EntryResource
    RELATIONSHIP_ENTRY_TYPES: Set[str] = {"references", "structures"}
    TOP_LEVEL_NON_ATTRIBUTES_FIELDS: Set[str] = {"id", "type", "relationships", "links"}

    @classmethod
    def all_aliases(cls) -> Tuple[Tuple[str, str]]:
        """Returns all of the associated aliases for this entry type,
        including those defined by the server config. The first member
        of each tuple is the OPTIMADE-compliant field name, the second
        is the backend-specific field name.

        Returns:
            A tuple of alias tuples.

        """
        from optimade.server.config import CONFIG

        return (
            tuple(
                (f"_{CONFIG.provider.prefix}_{field}", field)
                for field in CONFIG.provider_fields.get(cls.ENDPOINT, [])
            )
            + tuple(
                (f"_{CONFIG.provider.prefix}_{field}", field)
                for field in cls.PROVIDER_FIELDS
            )
            + tuple(CONFIG.aliases.get(cls.ENDPOINT, {}).items())
            + cls.ALIASES
        )

    @classproperty
    def SUPPORTED_PREFIXES(cls) -> Set[str]:
        """A set of prefixes handled by this entry type.

        !!! note
            This implementation only includes the provider prefix,
            but in the future this property may be extended to include other
            namespaces (for serving fields from, e.g., other providers or
            domain-specific terms).

        """
        from optimade.server.config import CONFIG

        return {CONFIG.provider.prefix}

    @classproperty
    def ALL_ATTRIBUTES(cls) -> Set[str]:
        """Returns all attributes served by this entry."""
        from optimade.server.config import CONFIG

        return (
            set(cls.ENTRY_RESOURCE_ATTRIBUTES)
            .union(
                cls.get_optimade_field(field)
                for field in CONFIG.provider_fields.get(cls.ENDPOINT, ())
            )
            .union(set(cls.get_optimade_field(field) for field in cls.PROVIDER_FIELDS))
        )

    @classproperty
    def ENTRY_RESOURCE_ATTRIBUTES(cls) -> Set[str]:
        from optimade.server.schemas import retrieve_queryable_properties

        return retrieve_queryable_properties(cls.ENTRY_RESOURCE_CLASS.schema())

    @classproperty
    def ENDPOINT(cls) -> str:
        return (
            cls.ENTRY_RESOURCE_CLASS.schema()
            .get("properties", {})
            .get("type", {})
            .get("const", "")
        )

    @classmethod
    def all_length_aliases(cls) -> Tuple[Tuple[str, str]]:
        """Returns all of the associated length aliases for this class,
        including those defined by the server config.

        Returns:
            A tuple of length alias tuples.

        """
        from optimade.server.config import CONFIG

        return cls.LENGTH_ALIASES + tuple(
            CONFIG.length_aliases.get(cls.ENDPOINT, {}).items()
        )

    @classmethod
    def length_alias_for(cls, field: str) -> Optional[str]:
        """Returns the length alias for the particular field,
        or `None` if no such alias is found.

        Parameters:
            field: OPTIMADE field name.

        Returns:
            Aliased field as found in [`all_length_aliases()`][optimade.server.mappers.entries.BaseResourceMapper.all_length_aliases].

        """
        return dict(cls.all_length_aliases()).get(field, None)

    @classmethod
    def get_backend_field(cls, optimade_field: str) -> str:
        """Return the field name configured for the particular
        underlying database for the passed OPTIMADE field name, that would
        be used in an API filter.

        Aliases are read from
        [`all_aliases()`][optimade.server.mappers.entries.BaseResourceMapper.all_aliases].

        If a dot-separated OPTIMADE field is provided, e.g., `species.mass`, only the first part will be mapped.
        This means for an (OPTIMADE, DB) alias of (`species`, `kinds`), `get_backend_fields("species.mass")`
        will return `kinds.mass`.

        Arguments:
            optimade_field: The OPTIMADE field to attempt to map to the backend-specific field.

        Examples:
            >>> get_backend_field("chemical_formula_anonymous")
            'formula_anon'
            >>> get_backend_field("formula_anon")
            'formula_anon'
            >>> get_backend_field("_exmpl_custom_provider_field")
            'custom_provider_field'

        Returns:
            The mapped field name to be used in the query to the backend.

        """
        split = optimade_field.split(".")
        alias = dict(cls.all_aliases()).get(split[0], None)
        if alias is not None:
            return alias + ("." + ".".join(split[1:]) if len(split) > 1 else "")
        return optimade_field

    @classmethod
    def alias_for(cls, field: str) -> str:
        """Return aliased field name.

        !!! warning "Deprecated"
            This method is deprecated could be removed without further warning. Please use
            [`get_backend_field()`][optimade.server.mappers.entries.BaseResourceMapper.get_backend_field].

        Parameters:
            field: OPTIMADE field name.

        Returns:
            Aliased field as found in [`all_aliases()`][optimade.server.mappers.entries.BaseResourceMapper.all_aliases].

        """
        warnings.warn(
            "The `.alias_for(...)` method is deprecated, please use `.get_backend_field(...)`.",
            DeprecationWarning,
        )
        return cls.get_backend_field(field)

    @classmethod
    def get_optimade_field(cls, backend_field: str) -> str:
        """Return the corresponding OPTIMADE field name for the underlying database field,
        ready to be used to construct the OPTIMADE-compliant JSON response.

        Aliases are read from
        [`all_aliases()`][optimade.server.mappers.entries.BaseResourceMapper.all_aliases].

        Arguments:
            backend_field: The backend field to attempt to map to an OPTIMADE field.

        Examples:
            >>> get_optimade_field("chemical_formula_anonymous")
            'chemical_formula_anonymous'
            >>> get_optimade_field("formula_anon")
            'chemical_formula_anonymous'
            >>> get_optimade_field("custom_provider_field")
            '_exmpl_custom_provider_field'

        Returns:
            The mapped field name to be used in an OPTIMADE-compliant response.

        """
        return {alias: real for real, alias in cls.all_aliases()}.get(
            backend_field, backend_field
        )

    @classmethod
    def alias_of(cls, field: str) -> str:
        """Return de-aliased field name, if it exists,
        otherwise return the input field name.

        !!! warning "Deprecated"
            This method is deprecated could be removed without further warning. Please use
            [`get_optimade_field()`][optimade.server.mappers.entries.BaseResourceMapper.get_optimade_field].

        Parameters:
            field: Field name to be de-aliased.

        Returns:
            De-aliased field name, falling back to returning `field`.

        """
        warnings.warn(
            "The `.alias_of(...)` method is deprecated, please use `.get_optimade_field(...)`.",
            DeprecationWarning,
        )
        return cls.get_optimade_field(field)

    @classmethod
    def get_required_fields(cls) -> set:
        """Get REQUIRED response fields.

        Returns:
            REQUIRED response fields.

        """
        return cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS

    @classmethod
    def map_back(cls, doc: dict) -> dict:
        """Map properties from MongoDB to OPTIMADE.

        Starting from a MongoDB document `doc`, map the DB fields to the corresponding OPTIMADE fields.
        Then, the fields are all added to the top-level field "attributes",
        with the exception of other top-level fields, defined in `cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS`.
        All fields not in `cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS` + "attributes" will be removed.
        Finally, the `type` is given the value of the specified `cls.ENDPOINT`.

        Parameters:
            doc: A resource object in MongoDB format.

        Returns:
            A resource object in OPTIMADE format.

        """
        mapping = ((real, alias) for alias, real in cls.all_aliases())
        newdoc = {}
        reals = {real for alias, real in cls.all_aliases()}
        for key in doc:
            if key not in reals:
                newdoc[key] = doc[key]
        for real, alias in mapping:
            if real in doc:
                newdoc[alias] = doc[real]

        if "attributes" in newdoc:
            raise Exception("Will overwrite doc field!")
        attributes = newdoc.copy()

        for field in cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS:
            value = attributes.pop(field, None)
            if value is not None:
                newdoc[field] = value
        for field in list(newdoc.keys()):
            if field not in cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS:
                del newdoc[field]

        newdoc["type"] = cls.ENDPOINT
        newdoc["attributes"] = attributes

        return newdoc
