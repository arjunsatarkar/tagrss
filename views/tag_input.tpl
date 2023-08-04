<div class="side-by-side-help-container tag-input-container">
    <label for="tags-input">{{get("label", "Tags:")}}</label>
    <noscript>
        <input type="text" name="{{input_name}}" value="{{get('input_value', '')}}" id="tags-input">
        % include("hover_help.tpl", text="Space-separated. Backslashes escape spaces.")
    </noscript>
    <span style="display: none;" id="tags-input-name-span">{{input_name}}</span>
    <span style="display: none;" id="tags-input-initial-value-span">{{get("input_value", "")}}</span>
</div>
