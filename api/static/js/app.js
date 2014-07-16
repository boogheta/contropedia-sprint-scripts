;(function(undefined) {

  // Namespace
  //-----------
  var app = {
    token: undefined,
    sigma: {
      instance: null,
      defaultSettings: {
        hideEdgesOnMove: true,
        defaultNodeColor: '#ccc'
      },
      forceAtlas2Settings: {}
    }
  };

  // Event listeners
  //-----------------

  // Enter key on url input
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

    $.post('/graph', data, onGraphReception);

    // Blurring input
    $(this).blur();
  });

  // On node doubleclick
  function onNodeDoubleClick(e) {
    console.log(e);
  }


  // Callbacks
  //-----------

  // When the graph is received from API
  function onGraphReception(response) {
    if (!app.token)
      app.token = response.token;

    // Instanciating sigma for the first time
    if (!app.sigma.instance) {
      app.sigma.instance = new sigma({
        container: document.getElementById('graph'),
        settings: app.sigma.defaultSettings
      });

      // Binding events
      app.sigma.instance.bind('doubleClickNode', onNodeDoubleClick);
    }

    var s = app.sigma.instance;

    // Adding nodes and edges
    response.graph.nodes.forEach(function(n) {

      // Not adding if node already exists
      if (s.graph.nodes(n.id) !== undefined)
        return;

      n.size = n.size || 1;
      s.graph.addNode(n);
    });

    response.graph.edges.forEach(function(e) {

      // Not adding if edge already exists
      if (s.graph.edges(e.id) !== undefined)
        return;

      s.graph.addEdge(e);
    });

    // Refreshing
    s.refresh();
  }

  // Exporting to window for convenience
  this.app = app;
}).call(this);
