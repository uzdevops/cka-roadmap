## A query language for JSON

Every `kubectl get ... -o json` is a JSON document, and JSONPath is the
small language for pulling one value out of it. Learn it on a plain
document first; the next lesson plugs it into kubectl.

```json
{
  "car": {
    "color": "blue",
    "price": "$20,000",
    "wheels": [
      {"model": "KDA", "location": "front-right"},
      {"model": "KDB", "location": "front-left"},
      {"model": "KDC", "location": "rear-right"},
      {"model": "KDD", "location": "rear-left"}
    ]
  },
  "bus": {"color": "white", "price": "$120,000"}
}
```

## Dictionaries: dots

```
$.car.color            →  "blue"
$.bus.price            →  "$120,000"
$.car                  →  the whole car object
```

`$` is the root of the document. A `.key` descends into a dictionary. The
result of a query is always a **list** of matches (`["blue"]`) - one match
here, possibly many below.

## Lists: brackets

```
$.car.wheels[0]        →  {"model": "KDA", "location": "front-right"}
$.car.wheels[0].model  →  "KDA"
$.car.wheels[*].model  →  ["KDA", "KDB", "KDC", "KDD"]     - * is "every element"
$.car.wheels[0,3]      →  elements 0 and 3
$.car.wheels[0:2]      →  elements 0 and 1 (end exclusive)
$.car.wheels[-1:]      →  the last element
```

A query on a top-level list starts with `$[...]`:

```json
["Apple", "Google", "Microsoft", "Amazon"]
```

```
$[0]                   →  "Apple"
$[1:3]                 →  ["Google", "Microsoft"]
$[*]                   →  everything
```

## Filters: conditions in brackets

```
$.car.wheels[?(@.location == "rear-right")].model     →  "KDC"
$[?(@ > 40)]                                           →  on a list of numbers: those above 40
```

`?()` introduces a filter; inside it, `@` means "the element being tested".
Operators: `==`, `!=`, `>`, `<`, `>=`, `<=`, and `in`/`nin` in some
implementations. Read `[?(@.location == "rear-right")]` as "the elements
whose location is rear-right".

## Wildcards and combinations

```
$.*.color                       →  ["blue", "white"]   - every top-level key's color
$.car.wheels[*].location        →  all four locations
$.car.wheels[?(@.model != "KDA")].location
```

## Putting it together

| Want | Query |
|---|---|
| the car's colour | `$.car.color` |
| every wheel model | `$.car.wheels[*].model` |
| the rear-left wheel's model | `$.car.wheels[?(@.location == "rear-left")].model` |
| the second wheel | `$.car.wheels[1]` |
| colours of every vehicle | `$.*.color` |

:::tip
Say the query aloud as a path: "root, car, wheels, every one of them,
model". If you can say it, you can write it. And remember the result is a
list, even for one match - that is why kubectl output often looks like
`[value]` until you learn to unwrap it.
:::

## Check yourself

1. Write the query for the price of the bus.
2. Write the query for the locations of all wheels.
3. Write the query for the model of the wheel whose location is
   `front-left`.
