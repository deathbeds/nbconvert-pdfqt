
LAB_STYLE = """
    body {
        --jp-layout-color0: transparent;
        --jp-layout-color1: transparent;
        --jp-layout-color2: transparent;
        --jp-layout-color3: transparent;
        --jp-cell-editor-background: transparent;
        --jp-border-width: 0;
        --jp-border-color0: transparent;
        --jp-border-color1: transparent;
        --jp-border-color2: transparent;
        --nbcqpdf-height: 1080px;
    }
    body,
    body .jp-ApplicationShell {
        width: 1920px;
        height: var(--nbcqpdf-height);
        min-height: var(--nbcqpdf-height);
        max-height: var(--nbcqpdf-height);
    }
    body .jp-InputArea-editor {
        border: 0;
        padding-left: 2em;
    }
    body .jp-LabShell.jp-mod-devMode {
        border: 0 !important;
    }
    body .jp-InputPrompt,
    body .jp-OutputPrompt {
        display: none;
        min-width: 0;
        max-width: 0;
    }
    body #jp-main-dock-panel {
        padding: 0;
    }
    body .jp-SideBar.p-TabBar,
    body #jp-top-panel,
    body .jp-Toolbar,
    body .p-DockPanel-tabBar,
    body .jp-Collapser {
        display: none;
        min-height: 0;
        max-height: 0;
        min-width: 0;
        max-width: 0;
    }
"""

FORCE_DEV = """
    var cfg = document.querySelector("#jupyter-config-data");
    if(cfg) {
        cfg.textContent = cfg.textContent.replace(
            `"devMode": "False"`,
            `"devMode": "True"`
        )
    }
"""

SINGLE_DOCUMENT = """
    ;(function(){
        var cmd = 'application:set-mode';
        var interval = setInterval(function(){
            var lab = window.lab
            if(
                !lab ||
                !lab.commands ||
                lab.commands.listCommands().indexOf(cmd) == -1
            ) {
                return;
            }
            clearInterval(interval);
            lab.shell.removeClass('jp-mod-devMode');
            lab.commands.execute(cmd, {mode: 'single-document'});
            if(document.querySelector('body[data-left-sidebar-widget]')) {
                lab.commands.execute('application:toggle-left-area');
            }
        }, 1000);
    })();
"""

MEASURE = """
    var bb = document.querySelector(".jp-Cell:last-child").getBoundingClientRect();
    var style = document.createElement('style');
    style.textContent = `body { --nbcqpdf-height: ${bb.bottom + 500}px; }`;
    document.body.appendChild(style);
    [bb.bottom, bb.right]
"""

RUN_ALL = """
    ;(function(){
        function evaluateXPath(aNode, aExpr) {
          var xpe = new XPathEvaluator();
          var nsResolver = xpe.createNSResolver(aNode.ownerDocument == null ?
            aNode.documentElement : aNode.ownerDocument.documentElement);
          var result = xpe.evaluate(aExpr, aNode, nsResolver, 0, null);
          var found = [];
          var res;
          while (res = result.iterateNext())
            found.push(res);
          return found;
        }

        var cmd = 'notebook:run-all-cells';
        var interval = setInterval(function(){
            var lab = window.lab
            if(
                !lab ||
                !lab.commands ||
                lab.commands.listCommands().indexOf(cmd) == -1
            ) {
                return;
            }
            if(!document.querySelector(`*[title="Kernel Idle"]`)){
                return;
            }
            clearInterval(interval);
            lab.commands.execute(cmd)
                .then(function(){
                    var busyInterval = setInterval(function(){
                        if(evaluateXPath(document, '//*[text() = "[*]:"]').length) {
                            return;
                        }
                        %s
                        lab.shell.mode = 'multiple-document';
                        lab.shell.mode = 'single-document';
                        clearInterval(busyInterval);
                        __QT__.measure();
                    }, 1000);
                })
        }, 1000);
    })();
""" % MEASURE


APPLY_STYLE = f"""
    var style = document.createElement("style");
    style.textContent = `{LAB_STYLE}`;
    document.body.appendChild(style);
    {SINGLE_DOCUMENT}
    {RUN_ALL}
"""

BRIDGE = """
new QWebChannel(qt.webChannelTransport, function(channel) {
    window.__QT__ = {
        print: function(text){
            channel.objects.page.print(text || "Hello World!");
        },
        measure: function(){
            channel.objects.page._measure();
        }
    }
    __QT__.print();
});
"""
