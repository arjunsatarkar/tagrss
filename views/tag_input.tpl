<div class="side-by-side-help-container">
    <label for="tag-input">{{get("label", "Tags:")}}</label>
    <input type="text" name="{{input_name}}" value="{{get('input_value', '')}}" id="tag-input">
    % include("hover_help.tpl", text="Space-separated. Backslashes escape spaces.")
</div>
