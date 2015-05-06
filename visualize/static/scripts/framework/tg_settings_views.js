"use strict";
/*
 * The following are small views used for manipulating various settings.
 */

var DefaultSettingsView = DefaultView.extend({
    modalTemplate:   "<div class=\"modal-dialog\">"+
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
    shortName: "login",
    
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
        this.userModel.on("change:loggedIn", this.render, this);
    },
    
    cleanup: function() {
        this.userModel.off(null, null, this);
    },
    
    render: function() {
        this.$el.html(this.modalTemplate);
        var container = d3.select(this.el);
        container.select(".modal-title").text(this.readableName);
        var body = container.select(".modal-body");
        
        if(this.userModel.get("loggedIn")) {
            body.html(this.logoutTemplate);
            var form = body.select("form");
            form.on("submit", function() {
                d3.event.preventDefault();
                this.userModel.submitQueryByHash({ logout: true }, function(data) {
                        if("logged_in" in data && !data["logged_in"]) {
                            globalUserModel.set({ loggedIn: false });
                        }
                    }, 
                    function(error){
                        form.select("#error-msg").text(error);
                    });
            }.bind(this));
        } else {
            body.html(this.loginTemplate);
            
            var form = body.select("form");
            var username = body.select("#username-input");
            var password = body.select("#password-input");
            
            form.on("submit", function() {
                d3.event.preventDefault();
                this.userModel.submitQueryByHash({username: username.property("value"), password: password.property("value") },
                    function(data) {
                        if("logged_in" in data && data["logged_in"]) {
                            globalUserModel.set({ loggedIn: true });
                        }
                    },
                    function(error) {
                        form.select("#error-msg").text(error);
                    });
            }.bind(this));
        }
    },
});

var EditFavoritesView = DefaultSettingsView.extend({
    readableName: "Edit Favorites",
    shortName: "edit_favs",
    
    render: function() {
        this.$el.html(this.modalTemplate);
        var container = d3.select(this.el);
        container.select(".modal-title").text(this.readableName);
        container.select(".modal-body").text("Edit favorites coming soon.");
    },
});
