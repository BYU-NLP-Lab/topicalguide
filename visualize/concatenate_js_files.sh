# Concatenate the list of files into one.

file_concat_list=(

static/scripts/libs/jquery-1.11.1.min.js
whitespace.txt
static/scripts/libs/lodash.min.js
whitespace.txt
static/scripts/libs/backbone.min.js
whitespace.txt
static/scripts/libs/d3.v3.min.js
whitespace.txt
static/scripts/libs/d3.layout.cloud.js
whitespace.txt
static/scripts/libs/d3.tip.v0.6.3.js
whitespace.txt
static/jquery-ui/jquery-ui.js
whitespace.txt
static/bootstrap/3.3.4/js/bootstrap.js
whitespace.txt
static/bootstrap-toggle/js/bootstrap-toggle.js
whitespace.txt

static/scripts/framework/tg_global.js
whitespace.txt
static/scripts/framework/tg_utilities.js
whitespace.txt
static/scripts/framework/tg_models.js
whitespace.txt
static/scripts/framework/tg_view_classes.js
whitespace.txt
static/scripts/framework/tg_framework_views.js
whitespace.txt
static/scripts/framework/tg_special_views.js
whitespace.txt
static/scripts/framework/tg_start.js
whitespace.txt
        
static/scripts/standard_views/home_view.js
whitespace.txt
#~ static/scripts/standard_views/datasets_view.js
#~ whitespace.txt
#~ static/scripts/standard_views/topics_view.js
#~ whitespace.txt
#~ static/scripts/standard_views/documents_view.js
#~ whitespace.txt
        #~ 
#~ static/scripts/visualizations/2dplots_view.js
#~ whitespace.txt
#~ static/scripts/visualizations/chord_view.js
#~ whitespace.txt
#~ static/scripts/visualizations/topics_over_time_view.js
#~ whitespace.txt
#~ static/scripts/visualizations/legend.js
#~ whitespace.txt
#~ static/scripts/visualizations/metadata_map_view.js
#~ whitespace.txt

)

#~ echo ${file_concat_list[@]}
cat ${file_concat_list[@]} >> one_file.js
