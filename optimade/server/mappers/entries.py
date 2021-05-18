from typing import Tuple, Optional
import warnings

__all__ = ("BaseResourceMapper",)


class BaseResourceMapper:
    """
    Generic Resource Mapper that defines and performs the mapping
    between objects in the database and the resource objects defined by
    the specification.

    Attributes:
        ENDPOINT (str): defines the endpoint for which to apply this
            mapper.
        ALIASES (Tuple[Tuple[str, str]]): a tuple of aliases between
            OPTIMADE field names and the field names in the database ,
            e.g. `(("elements", "custom_elements_field"))`.
        LENGTH_ALIASES (Tuple[Tuple[str, str]]): a tuple of aliases between
            a field name and another field that defines its length, to be used
            when querying, e.g. `(("elements", "nelements"))`.
            e.g. `(("elements", "custom_elements_field"))`.
        PROVIDER_FIELDS (Tuple[str]): a tuple of extra field names that this
            mapper should support when querying with the database prefix.
        REQUIRED_FIELDS (set[str]): the set of fieldnames to return
            when mapping to the OPTIMADE format.
        TOP_LEVEL_NON_ATTRIBUTES_FIELDS (set[str]): the set of top-level
            field names common to all endpoints.

    """

    ENDPOINT: str = ""
    ALIASES: Tuple[Tuple[str, str]] = ()
    LENGTH_ALIASES: Tuple[Tuple[str, str]] = ()
    PROVIDER_FIELDS: Tuple[str] = ()
    REQUIRED_FIELDS: set = set()
    TOP_LEVEL_NON_ATTRIBUTES_FIELDS: set = {"id", "type", "relationships", "links"}

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
        res = cls.TOP_LEVEL_NON_ATTRIBUTES_FIELDS.copy()
        res.update(cls.REQUIRED_FIELDS)
        return res

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
