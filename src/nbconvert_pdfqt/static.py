
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
}
body,
body .jp-ApplicationShell {
    width: 1920px;
    height: 2024px;
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
window.lab.shell.removeClass('jp-mod-devMode');
setTimeout(function(){
    window.lab.commands.execute('application:set-mode', {mode: 'single-document'});
    if(document.querySelector('body[data-left-sidebar-widget]')) {
        window.lab.commands.execute('application:toggle-left-area');
    }
}, %s);
"""

RUN_ALL = """
setTimeout(function(){
    console.error('running all cells');
    window.lab.commands.execute('notebook:run-all-cells');
}, 3000);
"""
