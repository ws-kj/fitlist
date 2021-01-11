var main = React.createClass({
    render: function() {
        return (
            <div class="box">
            <h1>Welcome to FitList</h1>
            <a href="/browse">Browse Workouts</a>
            </div>
        );
    }
});

ReactDOM.render(
    React.createElement(main, null),
    document.getElementById('content')
);
