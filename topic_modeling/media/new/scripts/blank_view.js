
var BlankView = DefaultView.extend({
    readableName: "Blank",
    
    initialize: function() {
    },
    
    render: function() {
        this.$el.html("<p>This is just a blank view.</p>");
    },
    
    renderHelpAsHtml: function() {
        return "<p>This is just a blank view.</p>";
    },
    
    cleanup: function() {
    },
});

globalViewModel.addViewClass([], BlankView);
