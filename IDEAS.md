#### Better syntax for rule triggers?
```py
@rule(not_found="program", changed=["a.cpp", "b.cpp"])

# defaults could be
@rule(always=None, dependencies=None, not_found=None, changed=None)
# and if every trigger is None, always will be set to True
```
