# Domain templates

All templates should be in the `templates` directory, and there can be multiple templates per file.

## Format

General format for domain templates:

```yml
- name: test-domain # Template name
  description: # Optional template description
  settings: # List of settings goes here
    - name: Setting A
      ...
    - name: Setting B
      ...
  template: |
    <j2 template goes here>
```

Settings are used to set jinja-variables to generate domain XML.

### Settings

Settings are built as follows:

```yml
- name: test # Setting name
  type: some_type # Setting type
  output: # Dictionary of output to jinja-variable mappings
    a: var_a
    b: var_b
    ...
  params: # Dictionary of parameters, depends on type
    min: 2
    selection:
      - a
      - b
      - c
      ...
    ...
    
```

- Simple settings: All have one output called `value`
  - `str` type is for any string input
  - `int` type is for an integer input, offers `min` and `max` parameters
  - `list` type specifies a set of options to choose from, offers `selection` parameter taking a list of string values.
  - `data` is for entering an amount of data i.e. as "10 GB", that will be transformed to a corresponding amount of bytes
  - `file` type is for picking a local file
- `volume` type allows picking and creating storage volumes. It has two outputs: `pool` and `volume`
- `network` type is used to pick a virtual network on the current connection. It has one output `network`

## Example

```yml
templates:
  - name: Minimal test
    description: Minimal
    settings:
      - name: A string field
        type: str
        output:
          value: str_val
      - name: An int field
        type: int
        output:
          value: int_val
        params:
          min: -3
          max: 42
      - name: A combo field
        type: list
        output:
          value: list_val
        params:
          selection:
            - a
            - b
            - c
      - name: A data field
        type: data
        output:
          value: data_val
      - name: A file field
        type: file
        output:
          value: file_val
      - name: Pick a volume
        type: volume
        output:
          pool: pool_val
          volume: vol_val
      - name: Pick a virtual network
        type: network
        output:
          network: network_val
    template: |
      String value is: {{ str_val }}
      Int value is: {{ int_val }}
      List value is: {{ list_val }}
      Data value is: {{ data_val }}
      File value is: {{ file_val }}
      The volume chosen is {{ vol_val }} in the pool {{ pool_val }}
      The network chosen is {{ network_val }}
```
