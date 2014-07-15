;(function(undefined) {

  // Namespace
  var app = {
    token: undefined
  };

  // Event listeners
  $('#url').keypress(function(e) {
    if (e.which !== 13)
      return;

    var url = $(this).val().trim();

    if (!url)
      return;

    // Requesting graph from api
    var data = {
      url: url
    };

    if (app.token)
      data.token = app.token;

    $.post('/graph', data, function(response) {
      console.log(response);
    });
  });
}).call(this);
