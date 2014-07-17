;(function(undefined) {

  // Namespace
  //-----------
  var app = {
    token: undefined,
    sigma: {
      instance: null,
      defaultSettings: {
        hideEdgesOnMove: true,
        defaultNodeColor: '#ccc',
        doubleClickEnabled: false
      },
      forceAtlas2Settings: {
        gravity: 0.1,
        slowDown: 2
      }
    }
  };

  var edgeId = 0;

  // Event listeners
  //-----------------

  // Enter key
  $('#url').keypress(function(e) {
    if (e.which !== 13)
      return;

    $('#go').trigger('click');
  });

  // Button
  $('#go').click(function(e) {
    var url = $('#url').val().trim();

    if (!url)
      return;

    // Requesting graph from api
    var data = {
      url: url
    };

    if (app.token)
      data.token = app.token;

    $.post('/graph', data, function(response) {
      if (response.error) {
        console.log(response.error, response.details);
        return;
      }

      // Setting token if this is the first API call
      if (!app.token)
        app.token = response.token;

      // Loading graph
      loadGraph(response.graph);
    });

    // Blurring input
    $('#url').blur();
  });

  // On node doubleclick
  function onNodeDoubleClick(e) {
    var data = {
      url: e.data.node.label,
      token: app.token
    };

    // API Call
    $.post('/graph', data, function(response) {
      if (response.error) {
        console.log(response.error, response.details);
        return;
      }

      // Loading graph
      loadGraph(response.graph);
    });
  }

  $('#bottom, #graph').mousedown(function(e) {
    e.preventDefault();
  });

  // Loading message
  $(document).ajaxStart(function() {
    $('#go').button('loading');
  });

  $(document).ajaxStop(function() {
    $('#go').button('reset');
  });

  // Callbacks
  //-----------

  // When the graph is received from API
  function loadGraph(graph) {

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

    // Killing forceAtlas2
    s.killForceAtlas2();

    // Adding nodes and edges
    graph.nodes.forEach(function(n) {

      // Casting to string id
      n.id += '';

      // Not adding if node already exists
      if (s.graph.nodes(n.id) !== undefined)
        return;

      n.size = n.size || 1;
      n.x = Math.random();
      n.y = Math.random();
      s.graph.addNode(n);
    });

    graph.edges.forEach(function(e) {

      // Attributing an arbitrary id
      e.id = ''+ (edgeId++);

      // Casting to string source and target
      e.source += '';
      e.target += '';

      // Checking existence of similar edge
      if (s.graph.hasSimilarEdge(e.source, e.target))
        return;

      s.graph.addEdge(e);
    });

    // Refreshing
    s.refresh();

    // Starting ForceAtlas
    s.startForceAtlas2(app.sigma.forceAtlas2Settings);
  }

  // Sigma's extensions
  //--------------------
  sigma.classes.graph.addMethod('hasSimilarEdge', function(s, t) {
    return !!this.allNeighborsIndex[s][t];
  });

  // Exporting to window for convenience
  this.app = app;
}).call(this);
