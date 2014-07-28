

var DocumentView = DefaultView.extend({
    
    readableName: "Documents",
    
    initialize: function() {
    },
    
    render: function() {
        this.$el.html("<p>Documents</p>");
    },
    
    cleanup: function() {
    }
    
});

// Add the Document View to the top level menu
globalViewModel.addViewClass([], DocumentView);
