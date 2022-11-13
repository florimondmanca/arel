
function arel_connect(isReconnect = false) {
    const reconnectInterval = parseFloat("$arel::reconnect_interval");
  
  const ws = new WebSocket("$arel::url");
  
  function log_info(msg) {
    console.info(`[arel] ${msg}`);
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
    if (event.data === "reload") {
      window.location.reload();
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
