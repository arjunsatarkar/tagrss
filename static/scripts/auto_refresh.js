(() => {
    const onFrontPage = () => {
        const searchParams = new URLSearchParams(window.location.search);
        const pageNum = searchParams.get("page_num");
        return (pageNum === "1") || (pageNum === null);
    };

    const refreshCheckboxLabel = document.querySelector("label#refresh_checkbox_label");
    if (onFrontPage()) {
        refreshCheckboxLabel.setAttribute("style", "");
    }

    const UPDATE_INTERVAL_MILLISECONDS = 1 * 60 * 1000; // 1 minute
    setInterval(async () => {
        if (!onFrontPage()) {
            return;
        }

        const refreshCheckbox = document.querySelector("label#refresh_checkbox_label > input");
        if (!refreshCheckbox.checked) {
            return;
        }

        console.log("Refreshing entries...");

        const response = await fetch(window.location);
        if (!response.ok) {
            return;
        }
        const responseText = await response.text();

        const parser = new DOMParser();
        const newDoc = parser.parseFromString(responseText, "text/html");
        document.querySelector("table").innerHTML = newDoc.querySelector("table").innerHTML;

        console.log("Refreshed entries.");
    }, UPDATE_INTERVAL_MILLISECONDS);
})();
