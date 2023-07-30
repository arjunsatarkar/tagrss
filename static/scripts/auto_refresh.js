(() => {
    const UPDATE_INTERVAL_MILLISECONDS = 1 * 60 * 1000; // 1 minute
    setInterval(async () => {
        const response = await fetch(window.location);
        if (!response.ok) {
            return;
        }
        const responseText = await response.text();

        const parser = new DOMParser();
        const newDoc = parser.parseFromString(responseText, "text/html");
        document.querySelector("table").innerHTML = newDoc.querySelector("table").innerHTML;
    }, UPDATE_INTERVAL_MILLISECONDS);
})();
