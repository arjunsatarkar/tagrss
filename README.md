# TagRSS

Extremely simple RSS reader with support for tags, which can be applied to multiple feeds.

This project is not in a finished state, but the core functionality is present.

## License

TagRSS is copyright (c) 2023-present Arjun Satarkar \<me@arjunsatarkar.net\>.

TagRSS is licensed under the GNU Affero General Public License v3.0, which requires among other things that "\[w\]hen a modified version is used to provide a service over a network, the complete source code of the modified version must be made available."[^1]

See `LICENSE.txt` in the root of this repository for the text of the license.

## To do

* Add JS to make the feed/tag input situation work like one would normally expect rather than like it's 1985. (Progressive enhancement, though.)
* Do more user input validation
* Handle more `requests` and `feedparser` error conditions
* Add some reasonably high internal limit on tag count
* Add support for authentication
* Allow specifying update interval on a per-feed basis

[^1]: https://choosealicense.com/licenses/agpl-3.0/
