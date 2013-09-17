## Tagify
Sublime Text 3 only.
Add tags to your code.
Put anywhere in your code `#@tagname` to create tag "tagname".

Python:
```python
#@todo
def someUnfinishedFunction():
    pass
```

JS:
```javaScript
// #@tag
```

HTML:
```html
<!-- #@tag -->
```

To gather summary press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> and run `Tagify: Get tag list` command. File names are double-clickable!

## Installation
For now clone this repo into packages.

## Todos
- [ ] Add config files with tagable files specified.
- [ ] Create ST3 package.
