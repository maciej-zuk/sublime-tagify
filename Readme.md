## Tagify
Working in Sublime Text 3. Probably in ST2 too.
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

To gather summary press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> and run `Tagify: Get tag list` command. File names are links!
Using <kbd>Ctrl</kbd>+<kbd>t</kbd> you can bring menu with common and recently used tags.

## Installation
Clone this repo into packages or search in package control.

## News
- 24 march 2017 - you can custimize tag re, also plaintext files support added
