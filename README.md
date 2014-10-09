
#### WARNING: Not yet fully tested!
----


#Python '15' puzzle solver

Python script based on [A* algorithm](http://en.wikipedia.org/wiki/A*_search_algorithm) to find solution of ['15' puzzle game](http://en.wikipedia.org/wiki/15_puzzle). Final solution (sequence of movements) is being visualized by PyQt. Whole script is works both on Windows and Linux (and maybe on Mac).


!['15' solver visualization](http://mhblog.cz/downloads/15solver.png)


### Main features

 * solver script is pure [Python 2.7](https://www.python.org/download/releases/2.7/), visualization is written in [PyQt4](http://www.riverbankcomputing.co.uk/software/pyqt/intro)
 * algorithm can be simply modified to solve other puzzle dimensions (3x3, 5x5, etc.)
 * algorithm uses associative arrays to speed up OPENED, CLOSED set searching


### Usage:

Edit the main part in solver.py!

```python
if __name__ == "__main__":
  # ---- SELECT only one heuristic function ------
  
  # calc_hfunc = calc_hfunc_positions
  calc_hfunc = calc_hfunc_manhattan
  # calc_hfunc = calc_hfunc_none
  
  # -------------------------------------------
  
  
  init_array = ([SPACER, 2, 3, 4], [6, 5, 10, 12], [9, 1, 8, 15], [13, 14, 7, 11])
  target_data = ([1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, SPACER])
  
  ...

```

### Requirments

* [Python 2.7](https://www.python.org/download)
* [PyQt4](http://www.riverbankcomputing.com/software/pyqt/download)


### License:

GNU GENERAL PUBLIC LICENSE

Version 2, June 1991
