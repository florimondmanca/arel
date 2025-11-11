function arel_connect(isReconnect = false) {
    const reconnectInterval = parseFloat("$arel::reconnect_interval");

    const ws = new WebSocket("$arel::url");

    function log_info(msg) {
        console.info(`[arel] ${msg}`);
    }

    function update_css(file) {
        // Appends the timestamp query string to file to force
        // the browser to reload the CSS file.

        const links = document.querySelectorAll(`link[href*="/${file}"]`);
        const timestamp = new Date().getTime();

        links.forEach(link => {
            const href = link.href.split('?')[0];
            const newHref = `${href}?${timestamp}`;
            log_info(`Updating CSS file ${href} to ${newHref}`);
            link.href = newHref;
        });
    }

    ws.onopen = function () {
        if (isReconnect) {
            // The server may have disconnected while it was reloading itself,
            // e.g. because the app Python source code has changed.
            // The page content may have changed because of this, so we don't
            // just want to reconnect, but also get that new page content.
            // A simple way to do this is to reload the page.
            window.location.reload();
            return;
        }

        log_info("Connected.");
    };

    ws.onmessage = function (event) {
        log_info(`Received message: ${event.data}`);
        // Commands:
        //   reload
        //   update_css:filename
        cmd = event.data.split(":")[0];

        switch (cmd) {
            case "reload":
                log_info("Reloading...");
                window.location.reload();
                break;
            case "update_css":
                file = event.data.split(":")[1];
                update_css(file);
                break;
            default:
                log_info("Received unknown command:", event.data);
        }
    };

    // Cleanly close the WebSocket before the page closes (1).
    window.addEventListener("beforeunload", function () {
        ws.close(1000);
    });

    ws.onclose = function (event) {
        if (event.code === 1000) {
            // Side-effect of (1). Ignore.
            return;
        }

        log_info(
            `WebSocket is closed. Will attempt reconnecting in ${reconnectInterval} seconds...`
        );

        setTimeout(function () {
            const isReconnect = true;
            arel_connect(isReconnect);
        }, reconnectInterval * 1000);
    };
}

arel_connect();
