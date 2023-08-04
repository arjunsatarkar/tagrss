"use strict";
(() => {
    const outerContainer = document.querySelector("div.tag-input-container");
    const rawInput = document.createElement("input");
    const name = outerContainer.querySelector("span#tags-input-name-span").innerText;
    rawInput.setAttribute("type", "hidden");
    rawInput.setAttribute("name", name);
    outerContainer.appendChild(rawInput);

    function parseSpaceSeparatedTags(inp) {
        const tags = new Set();
        let tag = ""
        let escaped = false;
        for (const c of inp) {
            switch (c) {
                case "\\":
                    if (!escaped) {
                        escaped = true;
                        continue;
                    }
                case " ":
                    if (!escaped) {
                        tags.add(tag);
                        tag = "";
                        continue;
                    }
            }
            escaped = false;
            tag += c;
        }
        if (tag) {
            tags.add(tag);
        }
        return Array.from(tags).sort((a, b) => a.localeCompare(b));
    }

    const dynamicInputContainer = document.createElement("span");

    function createDynamicInput() {
        const dynamicInput = document.createElement("input");
        dynamicInput.setAttribute("class", "dynamic-tag-input");
        // So autocomplete will work
        dynamicInput.setAttribute("name", "dynamic_tag_input");
        dynamicInput.addEventListener("input", handleInput);
        return dynamicInput;
    };

    function handleInput(e) {
        const sources = document.querySelectorAll("input.dynamic-tag-input");
        const lastDynamicInput = sources[sources.length - 1];
        if (e.currentTarget === lastDynamicInput && e.currentTarget.value) {
            dynamicInputContainer.appendChild(createDynamicInput());
        } else if (e.currentTarget === sources[sources.length - 2] && !e.currentTarget.value) {
            dynamicInputContainer.removeChild(lastDynamicInput);
        }
        let serialised = "";
        for (const [i, source] of sources.entries()) {
            const tag = source.value;
            if (!tag) { continue; }
            if (i > 0) {
                serialised += " ";
            }
            serialised += tag.replaceAll("\\", "\\\\").replaceAll(" ", "\\ ");
        }
        rawInput.value = serialised;
    };

    const firstDynamicInput = createDynamicInput();
    firstDynamicInput.setAttribute("id", "tags-input");
    dynamicInputContainer.appendChild(firstDynamicInput);

    const initialValue = outerContainer.querySelector("span#tags-input-initial-value-span").innerText;
    if (initialValue) {
        const tags = parseSpaceSeparatedTags(initialValue);
        let input = dynamicInputContainer.querySelector("input.dynamic-tag-input:last-of-type");
        for (const tag of tags) {
            input.value = tag;
            input = createDynamicInput();
            dynamicInputContainer.appendChild(input);
        }
    }

    outerContainer.appendChild(dynamicInputContainer);
})();
