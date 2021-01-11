# Contributing

The [Materials Consortia](https://github.com/Materials-Consortia) is very open to contributions to this package.

This may be anything from simple feedback and raising [new issues](https://github.com/Materials-Consortia/optimade-python-tools/issues/new) to creating [new PRs](https://github.com/Materials-Consortia/optimade-python-tools/compare).

Recommendations for setting up a development environment can be found in the [Installation instructions](https://www.optimade.org/optimade-python-tools/install/#full-development-installation).

## Getting Started with Filter Parsing and Transforming

Example use:

```python
from optimade.filterparser import LarkParser

p = LarkParser(version=(1, 0, 0))
tree = p.parse("nelements<3")
print(tree)
```

```shell
Tree('filter', [Tree('expression', [Tree('expression_clause', [Tree('expression_phrase', [Tree('comparison', [Tree('property_first_comparison', [Tree('property', [Token('IDENTIFIER', 'nelements')]), Tree('value_op_rhs', [Token('OPERATOR', '<'), Tree('value', [Tree('number', [Token('SIGNED_INT', '3')])])])])])])])])])
```

```python
print(tree.pretty())
```

```shell
filter
  expression
    expression_clause
      expression_phrase
        comparison
          property_first_comparison
            property	nelements
            value_op_rhs
              <
              value
                number	3
```

```python
tree = p.parse('_mp_bandgap > 5.0 AND _cod_molecular_weight < 350')
print(tree.pretty())
```

```shell
filter
  expression
    expression_clause
      expression_phrase
        comparison
          property_first_comparison
            property	_mp_bandgap
            value_op_rhs
              >
              value
                number	5.0
      expression_phrase
        comparison
          property_first_comparison
            property	_cod_molecular_weight
            value_op_rhs
              <
              value
                number	350
```

### Flow for Parsing User-Supplied Filter and Converting to Backend Query

`optimade.filterparser.LarkParser` will take user input to generate a `lark.Tree` and feed that to a `lark.Transformer`.
E.g., `optimade.filtertransformers.mongo.MongoTransformer` will turn the tree into something useful for your MongoDB backend:

```python
# Example: Converting to MongoDB Query Syntax
from optimade.filtertransformers.mongo import MongoTransformer

transformer = MongoTransformer()

tree = p.parse('_mp_bandgap > 5.0 AND _cod_molecular_weight < 350')
query = transformer.transform(tree)
print(query)
```

```json
{
    "$and": [
        {"_mp_bandgap": {"$gt": 5.0}},
        {"_cod_molecular_weight": {"$lt": 350.0}}
    ]
}
```


### Developing New Filter Transformers

If you would like to add a new transformer, please raise an issue to signal your intent (in case someone else is already working on this).
Adding a transformer requires the following:

1. A new submodule (`.py` file) in the `optimade/filtertransformers` folder containing an implementation of the transformer object, preferably one that extends `optimade.filtertransformers.base_transformer.BaseTransformer`.
2. Any additional Python requirements must be optional and provided as a separate "`extra_requires`" entry in `setup.py` and in the `requirements.txt` file.
3. Tests in `optimade/filtertransformers/tests` that are skipped if the required packages fail to import.

For examples, please check out existing filter transformers.
