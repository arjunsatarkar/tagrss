% import time
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Feed Entries | TagRSS</title>
    <link href="/static/styles/main.css" rel="stylesheet">
    <style>
        table {
            table-layout: fixed;
        }
        th#th-num {
            width: 2.5%;
        }
        th#th-title {
            width: 45%;
        }
        th#th-datetime {
            width: 12.5%;
        }
        th#th-tag {
            width: 20%;
        }
        td.td-tags > div {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: auto;
            white-space: nowrap;
        }
        th#th-feed {
            width: 20%;
        }
        td.td-feed > div {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: auto;
            white-space: nowrap;
        }

        label#refresh_checkbox_label {
            float: right;
        }
    </style>
    <script src="/static/scripts/auto_refresh.js" defer></script>
</head>
<body>
    <h1>TagRSS</h1>
    <nav>
        <p>
            <a href="/add_feed" class="no-visited-indication">Add feed</a>&nbsp;|
            <a href="/list_feeds" class="no-visited-indication">List feeds</a>
        </p>
    </nav>
    <label id="refresh_checkbox_label" style="display: none;">Refresh entries periodically
        <input type="checkbox" checked>
    </label>
    <details {{"open" if (included_feeds or included_tags) else ""}}>
        <summary>Filter</summary>
        <form>
            <div class="side-by-side-help-container">
                <label for="included-feeds-input">Included feeds:</label>
                <input type="text" name="included_feeds" value="{{' '.join([str(feed_id) for feed_id in included_feeds]) if included_feeds else ''}}" id="included-feeds-input">
                % include("hover_help.tpl", text="Space-separated feed IDs.")
            </div>
            % include(
            %     "tag_input.tpl",
            %     label="Included tags:",
            %     input_name="included_tags",
            %     input_value=included_tags_str if included_tags_str else ""
            % )
            <input type="submit" value="Filter">
            <input type="hidden" value="{{page_num}}" min="1" max="{{total_pages}}" name="page_num">
            <input type="hidden" value="{{per_page}}" min="1" max="{{max_per_page}}" name="per_page">
        </form>
        <form>
            <input type="hidden" name="included_feeds" value="">
            <input type="hidden" name="included_tags" value="">
            <input type="submit" value="Clear filters">
            <input type="hidden" value="{{page_num}}" min="1" max="{{total_pages}}" name="page_num">
            <input type="hidden" value="{{per_page}}" min="1" max="{{max_per_page}}" name="per_page">
        </form>
    </details>
    <table>
        <thead>
            <tr>
                <th id="th-num">#</th>
                <th id="th-title">Title</th>
                <th id="th-datetime">Date & Time ({{time.tzname[time.localtime().tm_isdst]}})</th>
                <th id="th-tags">Tags</th>
                <th id="th-feed">Feed</th>
            </tr>
        </thead>
        <tbody>
            % for i, entry in enumerate(entries):
                <tr>
                    <td>{{i + 1 + offset}}</td>
                    <td><a href="{{entry.link}}">{{entry.title}}</a></td>
                    <%
                        local_date = ""
                        utc_date = ""
                        epoch = entry.epoch_updated
                        if not epoch:
                            epoch = entry.epoch_published
                        end
                        if epoch:
                            local_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch))
                            utc_date = time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime(epoch))
                        end
                    %>
                    <td>
                        <time datetime="{{utc_date}}">{{local_date}}</time>
                    </td>
                    <td class="td-tags">
                        <div>
                            % tags = referenced_feeds[entry.feed_id].tags
                            % for i, tag in enumerate(tags):
                                % if i > 0:
                                    {{", "}}
                                % end
                                <span class="tag">{{tag}}</span>
                            % end
                        </div>
                    </td>
                    <td class="td-feed">
                        <div>
                            <a href="/manage_feed?feed={{entry.feed_id}}" class="no-visited-indication">⚙</a>
                            {{referenced_feeds[entry.feed_id].title}}
                            <small>(</small>{{entry.feed_id}}<small>)</small>
                        </div>
                    </td>
                </tr>
            % end
        </tbody>
    </table>
    <form>
        <label>Page
            <input type="number" value="{{page_num}}" min="1" max="{{total_pages}}" name="page_num">
        </label> of {{total_pages}}.
        <label>Per page:
            <input type="number" value="{{per_page}}" min="1" max="{{max_per_page}}" name="per_page">
        </label>
        <input type="submit" value="Go">
        % if included_feeds:
            <input type="hidden" name="included_feeds" value="{{included_feeds_str}}">
        % end
        % if included_tags:
            <input type="hidden" name="included_tags" value="{{included_tags_str}}">
        % end
    </form>
    % include("footer.tpl")
</body>
</html>
