// UNUSED, MEANT TO MAKE ANIMATED VIDS OF successive revisions of a page via phantomJs

var page = require('webpage').create(),
    system = require('system'),
    page_title, revid, url, output;

if (system.args.length < 3) {
    console.log('Usage: phantomjs wikiphantom.js <page_title> <rev_id>');
    phantom.exit(1);
}

page_title = system.args[1];
revid = system.args[2];
url = "https://en.wikipedia.org/w/index.php?title="+page_title+"&oldid="+revid;
output = 'data/'+page_title+'/screenshots/'+revid+'.png'
page.viewportSize = {width: 1024, height: 768};
page.clipRect = {top:0, left:0, width: 1024, height: 768};
page.open(url, function(status) {
    if (status !== 'success') {
        console.log('ERROR: Unable to load '+url);
        phantom.exit();
    }
    page.evaluate(function() {
        document.write(document.documentElement.outerHTML.replace(/<div id="contentSub".*(<div id="mw-content-text")/, "$1"));
    });
    //page.setContent(page.content.replace(/\n/, '').replace(/<div id="contentSub".*(<div id="mw-content-text")/, "$1"), url);
    page.render(output);
    phantom.exit();
});

