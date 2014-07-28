

var WordView = DefaultView.extend({
    
    readableName: "Words",
    
    initialize: function() {
    },
    
    render: function() {
        this.$el.html("<p>Words</p>");
    },
    
    cleanup: function() {
    }
    
});

// Add the Document View to the top level menu
globalViewModel.addViewClass([], WordView);
