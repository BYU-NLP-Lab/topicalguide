/*
 * The following are small views used for manipulating various settings.
 */

var HelpView = DefaultView.extend({
    readableName: "Help",
    
    template: 
"<div class=\"modal-dialog\">"+
"    <div class=\"modal-content\">"+
"        <div class=\"modal-header\">"+
"            <button type=\"button\" class=\"close\" data-dismiss=\"modal\"><span aria-hidden=\"true\">&times;</span><span class=\"sr-only\">Close</span></button>"+
"            <h3 class=\"modal-title\">Modal title</h3>"+
"        </div>"+
"        <div class=\"modal-body\">"+
"            Modal Body"+
"        </div>"+
"        <div class=\"modal-footer\">"+
"            <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>"+
"        </div>"+
"    </div>"+
"</div>",

    initialize: function() {
    },
    
    render: function() {
        this.$el.html(this.template);
        var container = d3.select(this.el);
        var title = container.select(".modal-title");
        title.text(globalViewModel.currentView.readableName + " Help");
        var body = container.select(".modal-body");
        body.html(globalViewModel.currentView.renderHelpAsHtml());
    },
    
    cleanup: function() {
    },
});

var FavoritesQuickSelectView = DefaultView.extend({
    readableName: "Favorites Quick Select",
    
    initialize: function() {
        this.selectionModel.on("change:dataset", this.forceHide, this);
        this.selectionModel.on("change:analysis", this.forceHide, this);
    },
    
    cleanup: function() {
        this.favsModel.off(null, null, this);
    },
    
    // Force the popover to hide if it needs to re-render.
    // It only re-renders if the user mouses over the popover button.
    forceHide: function() {
        $("#main-nav-favs").popover("hide");
    },
    
    render: function() {
        //~ this.favsModel.off(null, null, this); // Cleanup any events previously created by favicons.
        var that = this;
        this.$el.empty();
        // Create containers.
        d3.select(this.el).append("div")
            .attr("id", "favs-popover");
        
        var favorites = _.extend({}, this.favsModel.attributes);
        var topics = favorites.topics;
        var container = d3.select(this.el).select("#favs-popover").selectAll("div")
            .data(d3.entries(this.favsModel.attributes))
            .enter()
            .append("div");
        // Create headers.
        container.append("h5")
            .append("b")
            .text(function(d, i) { return d.key[0].toUpperCase() + d.key.slice(1); });
        // Create lists.
        container.each(function(d, i) {
            var el = d3.select(this);
            if(_.size(d.value) === 0) {
                el.append("p")
                    .text("No " + d.key);
            } else {
                el.append("ol")
                    .selectAll("li")
                    .data(function(d, i) { 
                        return d3.entries(d.value).map(function(entry) { 
                            entry.value = makeSingular(d.key);
                            return entry;
                        })
                    })
                    .enter()
                    .append("li")
                    .append("a")
                    .classed("nounderline pointer", true)
                    .text(function(d, i) { return d.key; })
                    // The onclick is triggered like this because the elements don't exist yet and so events cannot be bound to them.
                    .attr("onclick", function(d, i) { return "var hash = {}; hash['"+d.value+"'] = '"+d.key+"'; globalSelectionModel.set(hash);"; });
            }
        });
    },
});

var DefaultSettingsView = DefaultView.extend({
    template:   "<div class=\"modal-dialog\">"+
                "    <div class=\"modal-content\">"+
                "        <div class=\"modal-header\">"+
                "            <button type=\"button\" class=\"close\" data-dismiss=\"modal\"><span aria-hidden=\"true\">&times;</span><span class=\"sr-only\">Close</span></button>"+
                "            <h3 class=\"modal-title\"></h3>"+
                "        </div>"+
                "        <div class=\"modal-body\"></div>"+
                "        <div class=\"modal-footer\">"+
                "            <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\">Close</button>"+
                "        </div>"+
                "    </div>"+
                "</div>",
});

var LoginView = DefaultSettingsView.extend({
    readableName: "Login",
    
    loginTemplate:
"<form role=\"form\">"+
"    <div class=\"form-group\">"+
"        <label for=\"username-input\">Username:</label>"+
"        <input id=\"username-input\" type=\"text\" class=\"form-control\" placeholder=\"Enter your username here.\"></input>"+
"    </div>"+
"    <div class=\"form-group\">"+
"        <label for=\"password-input\">Password:</label>"+
"        <input id=\"password-input\" type=\"password\" class=\"form-control\" placeholder=\"Enter your password here.\"></input>"+
"    </div>"+
"    <button type=\"submit\" class=\"btn btn-default\">Login</button>"+
"    <label id=\"error-msg\" class=\"label label-danger\"></label>"+
"</form>",

    logoutTemplate:
"<form role=\"form\">"+
"    <button type=\"submit\" class=\"btn btn-default\">Logout</button>"+
"    <label id=\"error-msg\" class=\"label label-danger\"></label>"+
"</form>",

    initialize: function() {
        globalUserModel.on("change:loggedIn", this.render, this);
    },
    
    cleanup: function() {
        globalUserModel.off(null, null, this);
    },
    
    render: function() {
        this.$el.html(this.template);
        var container = d3.select(this.el);
        container.select(".modal-title").text(this.readableName);
        var body = container.select(".modal-body");
        
        if(globalUserModel.get("loggedIn")) {
            body.html(this.logoutTemplate);
            var form = body.select("form");
            form.on("submit", function() {
                d3.event.preventDefault();
                globalUserModel.submitQueryByHash({ logout: true }, function(data) {
                        if("logged_in" in data && !data["logged_in"]) {
                            globalUserModel.set({ loggedIn: false });
                        }
                    }, 
                    function(error){
                        form.select("#error-msg").text(error);
                    });
            });
        } else {
            body.html(this.loginTemplate);
            
            var form = body.select("form");
            var username = body.select("#username-input");
            var password = body.select("#password-input");
            
            form.on("submit", function() {
                d3.event.preventDefault();
                globalUserModel.submitQueryByHash({username: username.property("value"), password: password.property("value") },
                    function(data) {
                        if("logged_in" in data && data["logged_in"]) {
                            globalUserModel.set({ loggedIn: true });
                        }
                    },
                    function(error) {
                        form.select("#error-msg").text(error);
                    });
            });
        }
    },
});

var EditFavoritesView = DefaultSettingsView.extend({
    readableName: "Edit Favorites",
    
    render: function() {
        this.$el.html(this.template);
        var container = d3.select(this.el);
        container.select(".modal-title").text(this.readableName);
        container.select(".modal-body").text("Edit favorites coming soon.");
    },
});

/*
 * This allows new views or code to be loaded by the user.
 * It is disabled because there really isn't a need for it.
 * Also, it poses potential security threats.
 */
/*
var LoadScriptsView = DefaultSettingsView.extend({
    readableName: "Load Scripts",
    
    render: function() {
        this.$el.html(this.template);
        
        var container = d3.select(this.el);
        
        container.select(".modal-title").text(this.readableName);
        var body = container.select(".modal-body");
        body.html("");
        body.append("p")
            .classed("label-warning", true)
            .text("WARNING! Any script you load gains access to all data on this site. "+
                  "Some of the data could be data only accessible by your account and may include your username and password. "+
                  "Only load scripts from trusted sources. ");
        var form = body.append("form")
            .attr("role", "form");
        var group = form.append("div")
            .classed("form-group", true);
        group.append("label")
            .attr("for", "script-input")
            .text("Load Script:");
        var input = group.append("input")
            .attr("type", "text")
            .classed("form-control", true)
            .attr("id", "script-input")
            .attr("placeholder", "Enter the web address of the script...");
        form.append("button")
            .attr("type", "submit")
            .classed("btn btn-default", true)
            .text("Load");
            
        body.append("span")
            .classed("label", true)
            .attr("id", "load-script-feedback");
        
        form.on("submit", function() {
            d3.event.preventDefault();
            $.getScript(input.property("value"))
                .done(function(script, textStatus) {
                    body.select("#load-script-feedback")
                        .classed("label-success", true)
                        .classed("label-danger", false)
                        .text("Script loaded!");
                })
                .fail(function(jqxhr, settings, exception) {
                    body.select("#load-script-feedback")
                        .classed("label-danger", true)
                        .classed("label-success", false)
                        .text("Error: "+exception);
                });
        });
    },
});
*/

// Add when the DOM is ready so the modal elements are present.
$(function() {
    globalViewModel.setHelpViewClass(HelpView);
    globalViewModel.setFavoritesViewClass(FavoritesQuickSelectView);
    globalViewModel.addSettingsClass(LoginView);
    //~ globalViewModel.addSettingsClass(EditFavoritesView);
    //~ globalViewModel.addSettingsClass(LoadScriptsView);
});
