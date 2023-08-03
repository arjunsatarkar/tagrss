<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Add Feed | TagRSS</title>
    <link href="/static/styles/main.css" rel="stylesheet">
</head>
<body>
    <a href="/" class="no-visited-indication">&lt; home</a>
    % if get("after_add", False):
        <p><em>Added feed {{feed_source}}</em></p>
    % end
    <h1>Add a feed</h1>
    <form method="post">
        <div>
            <label for="feed-source-input">Source:</label>
            <input type="url" name="feed_source" id="feed-source-input">
        </div>
        % include("tag_input.tpl", input_name="tags")
        <div>
            <label for="title-input">Custom title (optional):</label>
            <input type="text" name="title" id="title-input">
        </div>
        <input type="submit" value="Add">
    </form>
    % include("footer.tpl")
</body>
</html>
