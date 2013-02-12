Visualizations
==============

In order to create a a new visualization, a few steps are needed:

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

  4. Include your javascript at the bottom of fancy.html

  		<script src="<filepath>" ></script>

3. Getting the data you need for the visualization

  1. Add an appropiate ajax url to the URLS[] variable in fancy.html

  2. Create a python function "my_fun()" in documents/ajax.py or topics/ajax.py that
      returns the data you need in a JSON format 

  3. Hook that url up to my_fun() in urls.py

  4. The data returned by my_fun is passed as a javascript object to the load() function
      inside of your visualization code

