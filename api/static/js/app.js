;(function(undefined) {

  // Namespace
  //-----------
  var app = {
    token: undefined,
    scale: chroma.scale(['wheat', 'maroon']),
    maxControversiality: 6,
    sigma: {
      instance: null,
      defaultSettings: {
        maxEdgeSize: 0.05,
        hideEdgesOnMove: true,
        defaultNodeColor: '#ccc',
        defaultEdgeColor: '#ccc',
        doubleClickEnabled: false,
        minNodeSize: 3
      },
      forceAtlas2Settings: {
        gravity: 0.001,
        strongGravityMode: true
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

      // Setting max contro
      app.maxControversiality = response.max_contro || app.maxControversiality;

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

      // Setting max contro
      app.maxControversiality = response.max_contro || app.maxControversiality;

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
      n.co = +n.co || 0;
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

      e.color = app.sigma.defaultSettings.defaultEdgeColor;

      // Checking existence of similar edge
      if (s.graph.hasSimilarEdge(e.source, e.target))
        return;

      s.graph.addEdge(e);
    });

    // Updating maxContro
    app.maxControversiality = Math.max.apply(Math, s.graph.nodes().map(function(n) { return n.co; }));

    // Adjusting size and color of nodes
    s.graph.nodes().forEach(function(n) {
      n.size = s.graph.degree(n.id, 'out');
      n.color = app.scale(n.co / app.maxControversiality).hex()
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
