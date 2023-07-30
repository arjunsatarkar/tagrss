<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>List Feeds | TagRSS</title>
    <link href="/static/styles/main.css" rel="stylesheet">
    <style>
        table {
            table-layout: fixed;
        }
        th#th-num {
            width: 2.5%;
        }
        th#th-id {
            width: 2.5%;
        }
        th#th-title {
            width: 50%;
        }
        th#th-tag {
            width: 35%;
        }
        td.td-tags > div {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: auto;
            white-space: nowrap;
        }
        th#th-source {
            width: 5%;
        }
        th#th-manage {
            width: 5%;
        }
    </style>
</head>
<body>
    <a href="/" class="no-visited-indication">&lt; home</a>
    <h1>Feeds</h1>
    <table>
        <thead>
            <tr>
                <th id="th-num">#</th>
                <th id="th-id">ID</th>
                <th id="th-feed">Feed</th>
                <th id="th-tags">Tags</th>
                <th id="th-source">Source</th>
                <th id="th-manage">Manage</th>
            </tr>
        </thead>
        <tbody>
            % for i, feed in enumerate(feeds):
                <tr>
                    <td>{{i + 1 + offset}}</td>
                    <td>{{feed["id"]}}</td>
                    <td>{{feed["title"]}} (<a href="/?included_feeds={{feed['id']}}" class="no-visited-indication">filter</a>)</td>
                    <td class="td-tags">
                        <div>
                            % tags = core.get_feed_tags(feed["id"])
                            % for i, tag in enumerate(tags):
                                % if i > 0:
                                    {{", "}}
                                % end
                                <span class="tag">{{tag}}</span>
                            % end
                        </div>
                    </td>
                    <td><a href="{{feed['source']}}" class="no-visited-indication">🔗</a></td>
                    <td><a href="/manage_feed?feed={{feed['id']}}" class="no-visited-indication">⚙</a></td>
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
    </form>
    % include("footer.tpl")
</body>
</html>
