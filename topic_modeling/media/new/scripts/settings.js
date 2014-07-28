
var LoginView = LoadingView.extend({
    readableName: "Login",
    
    render: function() {
        this.$el.html("Login Panel!");
    },
});

globalViewModel.addSettingsClass(LoginView);
