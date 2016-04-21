# Topical Guide Style Guide

This document contains guidelines for code style when working with the Topical Guide code.

## Javascript Style Guide

  + indentation must be two spaces
  + never use semicolons
  + include space after opening brace and before closing brace:  `[ 1, 2, 3 ]`
  + always include one space after a keyword
  + prefer named functions over assigning anonymous functions:
    ```
    function doStuff() {
      ...
    }
    var f = doStuff
    ```
  + always use threequals (`===`)

## Python Style Guide

Follow PEP 8, except that hanging indentation with function parameters must be aligned according to the first parameter:
```
results = applyalgorithm(first,
                         second,
                         third)
```
