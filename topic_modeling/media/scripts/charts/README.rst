Visualizations
==============

In order to create a anew visualization, a few steps are needed:

1. make a new JS file with the following template: (viz.js.example)

.. include:: viz.js.example
  :code: js

2. Add the HTML stuff: in templates/fancy.html

  1. Controls:

      in <div id="controls"></div> that looks like <div id="controls-[name]"></div>

  2. Infos:

      in <div id="info"></div> that looks like <div id="controls-[name]"></div>
  
  3. Menu:
      
      in div.navbar-inner.container like <div id="menu-[name]"></div>

